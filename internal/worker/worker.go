package worker

// Worker interface
type Worker interface {

	//Initializes the worker with machine specs
	InitWorker(*RestClient) (*WorkerImpl, error)

	//Registers the worker with the master
	RegisterWorker() (*int, error)

	//Requests work from the master
	GetWork() (*WorkPackage, error)

	//Executes the work package
	ExecuteWork(*WorkPackage) []WorkResult

	//TODO: Heartbeat (pulses)
}
