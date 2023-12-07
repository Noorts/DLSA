package worker

import (
	"bytes"
	"fmt"
	"os/exec"
	"strings"

	"github.com/zcalusic/sysinfo"
)

// Maybe we should define some sort of score?
type MachineSpecs struct {
	cores        uint    // Number of cores
	cpus         uint    // Number of CPUs
	threads      uint    // Number of threads
	memory_speed uint    // Memory speed in MHz
	memory_size  uint    // Amount of RAM in MB
	gpu          uint    // 0 if no GPU, 1 if GPU
	benchmark    float32 // Benchmark to run
}

func GetMachineSpecs(benchmark float32) (*MachineSpecs, error) {
	var si sysinfo.SysInfo
	gpu := checkGPU() //Not sure about this tbh
	si.GetSysInfo()
	specs := MachineSpecs{
		cores:        si.CPU.Cores,
		cpus:         si.CPU.Cpus,
		threads:      si.CPU.Threads,
		memory_speed: si.Memory.Speed,
		memory_size:  si.Memory.Size,
		gpu:          gpu,
		benchmark:    benchmark,
	}
	return &specs, nil

}

func checkGPU() uint {
	cmd := exec.Command("nvidia-smi")
	var out bytes.Buffer
	cmd.Stdout = &out
	err := cmd.Run()
	if err != nil {
		fmt.Println("Error executing nvidia-smi command:", err)
		return 0
	}

	output := out.String()
	// This is a very basic check and might need to be adjusted
	// depending on your system and the output of nvidia-smi.
	if strings.Contains(output, "NVIDIA-SMI") {
		return 1
	} else {
		return 0
	}
}
