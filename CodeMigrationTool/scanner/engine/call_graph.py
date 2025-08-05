import os
import json

class CallGraphGenerator:
    def __init__(self, config_path='config.yml'):
        import yaml
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.source_path = self.config['source_code_base']
        self.output_path = './output'

    def generate(self):
        print("[CallGraph] Starting call graph generation...")
        call_graph = {}

        for root, _, files in os.walk(self.source_path):
            for file in files:
                if file.endswith('.java'):
                    class_name = os.path.splitext(file)[0]
                    call_graph[class_name] = {
                        "calls": [],
                        "file": os.path.relpath(os.path.join(root, file), self.source_path)
                    }

        output_file = os.path.join(self.output_path, 'call_graph.json')
        with open(output_file, 'w') as f:
            json.dump(call_graph, f, indent=2)

        print(f"[CallGraph] Call graph saved to {output_file}")
