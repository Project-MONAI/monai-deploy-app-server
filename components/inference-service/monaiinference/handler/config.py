class Config:

    def __init__(self, map_urn, map_entrypoint, map_cpu, map_memory, map_gpu, map_input_path, map_output_path,
                 payload_host_path):
        self.map_urn = map_urn
        self.map_entrypoint = map_entrypoint
        self.map_cpu = map_cpu
        self.map_memory = map_memory
        self.map_gpu = map_gpu
        self.map_input_path = map_input_path
        self.map_output_path = map_output_path
        self.payload_host_path = payload_host_path
