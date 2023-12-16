use reqwest::blocking::Client;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::error::Error;
use uuid::Uuid;

type Sequence = String;
type SequenceId = String;

#[derive(Serialize, Deserialize, Debug)]
pub struct QueryTargetType {
    pub query: SequenceId,
    pub target: SequenceId,
}

#[derive(Serialize, Deserialize)]
pub struct Alignment {
    pub alignment_string: String,
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

#[derive(Serialize, Deserialize)]
struct CompleteWorkPackage {
    #[serde(flatten)]
    work_package: WorkPackage,
    sequences: HashMap<SequenceId, Sequence>,
}

#[derive(Serialize, Deserialize)]
pub struct MachineSpecs {
    pub benchmark_result: f32,
}

#[derive(Serialize, Deserialize)]
struct WorkRequest {
    id: String,
}

#[derive(Serialize, Deserialize)]
struct Heartbeat {
    worker_id: String,
}

#[derive(Serialize, Deserialize)]
pub struct TargetQueryCombination {
    pub target: SequenceId,
    pub query: SequenceId,
}

#[derive(Serialize, Deserialize)]
pub struct WorkResult {
    pub alignments: Vec<AlignmentDetail>,
}

#[derive(Serialize, Deserialize)]
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
        println!("Got work: {:?}", res);
        // Parse the JSON response
        let work_package: Option<WorkPackage> = res.json()?;
        Ok(work_package)
    }

    pub fn get_sequence(
        &self,
        package_id: String,
        query: SequenceId,
        worker_id: String,
    ) -> Result<Sequence, Box<dyn Error>> {
        //TODO: Is it query or &query?

        let url = format!(
            "{}/work/{}/sequence/{}/{}",
            self.base_url, query, worker_id, package_id,
        );
        let res = self.client.get(&url).send()?;
        let sequence: Sequence = res.json()?;
        println!("Got sequence: {:?}", sequence);
        Ok(sequence)
    }

    pub fn send_work_result(
        &self,
        work_result: WorkResult,
        work_id: &String,
    ) -> Result<(), Box<dyn Error>> {
        let url = format!("{}/work/{}/result", self.base_url, work_id);
        let res = self.client.post(&url).json(&work_result).send()?;
        Ok(())
    }

    fn start_heartbeat_routine(&self, interval: u64, worker_id: String) {
        //TODO: While alive?
        loop {
            //TODO: Speciy thread or what
            std::thread::sleep(std::time::Duration::from_secs(interval));
            self.send_pulse(&worker_id);
        }
    }

    //TODO: Ask Daniel why I had to to &String, can
    fn send_pulse(&self, worker_id: &String) -> Result<(), Box<dyn Error>> {
        let url = format!("{}/worker/pulse", self.base_url);
        let res = self
            .client
            .post(&url)
            .json(&Heartbeat {
                worker_id: worker_id.clone(),
            })
            .send()?;
        //Return res?
        Ok(())
    }
}
