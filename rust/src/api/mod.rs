use reqwest::blocking::Client;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::error::Error;
use std::sync::Arc;
use uuid::Uuid;

pub type Sequence = String;
pub type SequenceId = String;

#[derive(Serialize, Deserialize, Debug)]
pub struct QueryTargetType {
    pub query: SequenceId,
    pub target: SequenceId,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Alignment {
    pub alignment: String,
    pub length: i16,
    pub score: i16,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct WorkPackage {
    pub id: Option<String>,
    pub job_id: Option<String>,
    pub queries: Vec<QueryTargetType>,
    pub match_score: i16,
    pub mismatch_penalty: i16,
    pub gap_penalty: i16,
}

// #[derive(Serialize, Deserialize)]
pub struct CompleteWorkPackage<'a> {
    // #[serde(flatten)]
    pub work_package: &'a mut WorkPackage,
    pub sequences: HashMap<SequenceId, Sequence>,
}

#[derive(Serialize, Deserialize)]
pub struct MachineSpecs {
    pub benchmark_result: i32,
}

#[derive(Serialize, Deserialize)]
struct WorkRequest {
    id: String,
}

#[derive(Serialize, Deserialize)]
pub struct Heartbeat {
    pub id: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct TargetQueryCombination {
    pub target: SequenceId,
    pub query: SequenceId,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct WorkResult {
    pub alignments: Vec<AlignmentDetail>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct AlignmentDetail {
    pub combination: TargetQueryCombination,
    pub alignment: Alignment,
}

// RestClient definition will follow
pub struct RestClient {
    base_url: String,
    client: Client,
}

impl RestClient {
    pub fn new(base_url: String) -> RestClient {
        RestClient {
            base_url,
            client: Client::new(),
        }
    }

    pub fn register_worker(&self, specs: MachineSpecs) -> Result<String, Box<dyn Error>> {
        let url = format!("{}/worker/register", self.base_url);

        let res = self.client.post(&url).json(&specs).send()?;

        let map = res.json::<HashMap<String, String>>()?;
        let worker_id = map.get("id").unwrap().clone();
        Ok(worker_id)
    }

    pub fn get_work(&self, worker_id: &String) -> Result<Option<WorkPackage>, Box<dyn Error>> {
        let url = format!("{}/work/", self.base_url);

        // Send the request and get the response synchronously
        let res = self
            .client
            .post(&url)
            .json(&WorkRequest {
                id: worker_id.clone(),
            })
            .send()?; // This is a synchronous call
                      // Parse the JSON response
        let work_package: Option<WorkPackage> = res.json()?;
        Ok(work_package)
    }

    pub fn get_sequence(
        &self,
        package_id: &String,
        query: &SequenceId,
        worker_id: &str,
    ) -> Result<Sequence, Box<dyn Error>> {
        //TODO: Is it query or &query?

        let url = format!(
            "{}/work/{}/sequence/{}/{}",
            self.base_url, package_id, query, worker_id,
        );
        let res = self.client.get(&url).send()?;
        let sequence: Sequence = res.json()?;
        Ok(sequence)
    }

    pub fn send_work_result(
        &self,
        work_result: WorkResult,
        work_id: &String,
    ) -> Result<(), Box<dyn Error>> {
        // println!("work_id: {}", work_id);
        let url = format!("{}/work/{}/result", self.base_url, work_id);
        // println!("Sending work result to {}", url);
        // println!("Work result json: {:?}", work_result);
        // println!(
        //     "First query: {:?}",
        //     work_result.alignments[0].combination.query
        // );
        // println!(
        //     "First target: {:?}",
        //     work_result.alignments[0].combination.target
        // );

        let res = self.client.post(&url).json(&work_result).send()?;
        // println!("Work result sent: {:?}", res);
        // println!("Status: {:?}", res.status());

        Ok(())
    }

    pub fn send_pulse(&self, worker_id: &String) -> Result<(), Box<dyn Error>> {
        let url = format!("{}/worker/pulse", self.base_url);
        let res = self
            .client
            .post(&url)
            .json(&Heartbeat {
                id: worker_id.clone(),
            })
            .send()?;
        //Return res?
        println!("Pulse sent: {:?}", res);
        Ok(())
    }
}
