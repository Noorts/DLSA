package worker

// Worker interface
type WorkerInterface interface {

	//Initializes the worker with machine specs
	InitWorker(*RestClient) (*Worker, error)

	//Registers the worker with the master
	RegisterWorker() (*int, error)

	//Requests work from the master
	GetWork() (*WorkPackage, error)

	//Executes the work package
	ExecuteWork(*WorkPackage) []WorkResult

	//Sends a heartbeat to the master
	Heartbeat() error
}
