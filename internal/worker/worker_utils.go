package worker

import "github.com/zcalusic/sysinfo"

// Maybe we should define some sort of score?
type MachineSpecs struct {
	cores        uint // Number of cores
	cpus         uint // Number of CPUs
	threads      uint // Number of threads
	memory_speed uint // Memory speed in MHz
	memory_size  uint // Amount of RAM in MB
}

func GetMachineSpecs() (*MachineSpecs, error) {
	var si sysinfo.SysInfo
	si.GetSysInfo()
	specs := MachineSpecs{
		cores:        si.CPU.Cores,
		cpus:         si.CPU.Cpus,
		threads:      si.CPU.Threads,
		memory_speed: si.Memory.Speed,
		memory_size:  si.Memory.Size,
	}
	return &specs, nil

}
