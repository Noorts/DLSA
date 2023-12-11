package worker

// Maybe we should define some sort of score?
type MachineSpecs struct {
	benchmark float32 // Benchmark to run
}

func GetMachineSpecs(benchmark float32) *MachineSpecs {
	return &MachineSpecs{
		benchmark: benchmark,
	}
}
