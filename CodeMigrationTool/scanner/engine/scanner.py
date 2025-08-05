import os
import re
import json
import yaml
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from .logger import log_time

class Scanner:
    def __init__(self, config_path='config.yml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.source_path = self.config['source_code_base']
        self.output_path = self.config['output_dir']
        self.project_root_dir = self.config.get('project_root_dir')  # NEW

        os.makedirs(self.output_path, exist_ok=True)

        # Outputs
        self.file_metadata = []
        self.call_graph = {}
        self.class_dependencies = {}
        self.interface_implementations = {}
        self.type_index = {}

        # New analysis
        self.fat_actions = []
        self.manual_singletons = []
        self.static_utils = []
        self.jndi_lookups = []
        self.manual_daos = []

        # Patterns
        self.class_pattern = re.compile(r'\bclass\s+(\w+)\s*(?:extends\s+(\w+))?\s*(?:implements\s+([\w,\s]+))?')
        self.interface_pattern = re.compile(r'\binterface\s+(\w+)')
        self.import_pattern = re.compile(r'import\s+([\w\.]+);')
        self.new_pattern = re.compile(r'new\s+(\w+)\s*\(')
        self.singleton_pattern = re.compile(r'private\s+static\s+(\w+)\s+(\w+);')
        self.get_instance_pattern = re.compile(r'public\s+static\s+\w+\s+getInstance')
        self.jndi_pattern = re.compile(r'new\s+InitialContext\(\).*?\.lookup\(["\'](.+?)["\']')

    def classify(self, content):
        if 'extends Action' in content or 'ActionForm' in content:
            return 'Action'
        if 'implements Serializable' in content and 'Form' in content:
            return 'Form'
        if 'DAO' in content:
            return 'DAO'
        if 'Service' in content:
            return 'Service'
        if 'interface' in content:
            return 'Interface'
        return 'Class'

    def get_project_relative_path(self, abs_path):
        """
        Extracts relative path starting from configured project_root_dir (e.g., 'struts-crud-master/...').
        """
        if self.project_root_dir:
            index = abs_path.find(self.project_root_dir)
            if index != -1:
                return abs_path[index:]
        return os.path.basename(abs_path)  # fallback

    @log_time
    def process_java_file(self, abs_path, rel_path):
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.file_metadata.append({
                "filename": os.path.basename(abs_path),
                "extension": ".java",
                "absolute_path": os.path.abspath(abs_path),
                "relative_path": os.path.relpath(abs_path, self.source_path)
            })

            detected_type = self.classify(content)
            class_match = self.class_pattern.search(content)
            interface_match = self.interface_pattern.search(content)

            class_name = None
            implements = []
            if class_match:
                class_name = class_match.group(1)
                if class_match.group(3):
                    implements = [i.strip() for i in class_match.group(3).split(',')]

            if interface_match:
                class_name = interface_match.group(1)
                detected_type = "Interface"

            imports = self.import_pattern.findall(content)
            news = self.new_pattern.findall(content)
            used_classes = list(set(imports + news))

            if class_name:
                self.call_graph[class_name] = {"calls": used_classes, "file": rel_path}
                self.class_dependencies[class_name] = used_classes
                self.type_index[class_name] = detected_type
                for i in implements:
                    self.interface_implementations.setdefault(i, []).append(class_name)

            # Fat Action Logic
            if detected_type == "Action" and 'execute' in content:
                lines = content.splitlines()
                exec_lines = [i for i, l in enumerate(lines) if 'execute(' in l]
                if exec_lines:
                    start = exec_lines[0]
                    method_body = lines[start:]
                    brace_count = 0
                    count = 0
                    for line in method_body:
                        count += 1
                        brace_count += line.count('{') - line.count('}')
                        if brace_count == 0:
                            break
                    if count > 30:
                        self.fat_actions.append({"class": class_name, "line_count": count, "file": rel_path})

            # Manual Singleton
            if self.singleton_pattern.search(content) and self.get_instance_pattern.search(content):
                self.manual_singletons.append({"class": class_name, "file": rel_path})

            # Static Utility
            if " class " in content and "static" in content and "public" in content:
                static_methods = re.findall(r'public\s+static\s+\w+', content)
                all_methods = re.findall(r'public\s+\w+', content)
                if len(static_methods) >= len(all_methods) * 0.8:
                    self.static_utils.append({"class": class_name, "file": rel_path})

            # JNDI Lookup
            jndi_matches = self.jndi_pattern.findall(content)
            for jndi in jndi_matches:
                self.jndi_lookups.append({"class": class_name, "lookup": jndi, "file": rel_path})

            # Manual DAO/Service creation
            for cls in used_classes:
                if cls.endswith("DAO") or cls.endswith("Service"):
                    self.manual_daos.append({
                        "consumer": class_name,
                        "instantiates": cls,
                        "file": rel_path
                    })

        except Exception as e:
            print(f"[ERROR] [{os.path.basename(abs_path)}] Failed to process: '{rel_path}' - {e}")

    def parse_java_files(self):
        java_files = []
        for root, _, files in os.walk(self.source_path):
            for file in files:
                if file.endswith(".java"):
                    abs_path = os.path.join(root, file)
                    rel_path = self.get_project_relative_path(abs_path)
                    java_files.append((abs_path, rel_path))

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(self.process_java_file, f, r) for f, r in java_files]
            for _ in as_completed(futures):
                pass

    def parse_jsp_files(self):
        taglibs = []
        for root, _, files in os.walk(self.source_path):
            for file in files:
                if file.endswith(".jsp"):
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if '<html:' in content or '<bean:' in content:
                            rel_path = self.get_project_relative_path(path)
                            taglibs.append({"file": rel_path})
        with open(os.path.join(self.output_path, "taglib_usage_report.json"), "w") as f:
            json.dump(taglibs, f, indent=2)

    def parse_struts_config(self):
        output = {}
        unmapped = []
        detected_actions = {cls for cls, t in self.type_index.items() if t == "Action"}

        for root, _, files in os.walk(self.source_path):
            for file in files:
                if file.lower() == "struts-config.xml":
                    file_path = os.path.join(root, file)
                    tree = ET.parse(file_path)
                    xml_root = tree.getroot()
                    for action in xml_root.findall(".//action-mappings/action"):
                        path = action.attrib.get("path")
                        action_type = action.attrib.get("type")
                        name = action.attrib.get("name")
                        scope = action.attrib.get("scope")
                        input_page = action.attrib.get("input")
                        forwards = {f.attrib["name"]: f.attrib["path"] for f in action.findall("forward")}
                        output[path] = {
                            "type": action_type,
                            "form": name,
                            "scope": scope,
                            "input": input_page,
                            "forwards": forwards
                        }
                    config_classes = {v["type"] for v in output.values()}
                    unmapped = sorted(list(detected_actions - config_classes))
                    break

        with open(os.path.join(self.output_path, "struts_config_map.json"), "w") as f:
            json.dump(output, f, indent=2)
        with open(os.path.join(self.output_path, "unmapped_actions.json"), "w") as f:
            json.dump(unmapped, f, indent=2)

    def parse_tiles_defs(self):
        output = {}
        for root, _, files in os.walk(self.source_path):
            for file in files:
                if file.lower() == "tiles-defs.xml":
                    file_path = os.path.join(root, file)
                    tree = ET.parse(file_path)
                    xml_root = tree.getroot()
                    for definition in xml_root.findall(".//definition"):
                        name = definition.attrib.get("name")
                        template = definition.attrib.get("template")
                        puts = {p.attrib["name"]: p.attrib["value"] for p in definition.findall("put")}
                        output[name] = {"template": template, "puts": puts}
                    break

        with open(os.path.join(self.output_path, "tiles_definitions.json"), "w") as f:
            json.dump(output, f, indent=2)

    def run(self):
        self.parse_java_files()
        self.parse_jsp_files()
        self.parse_struts_config()
        self.parse_tiles_defs()

        self._save("file_metadata.json", self.file_metadata)
        self._save("call_graph.json", self.call_graph)
        self._save("class_dependencies.json", self.class_dependencies)
        self._save("interface_implementations.json", self.interface_implementations)
        self._save("type_index.json", self.type_index)

        self._save("fat_actions.json", self.fat_actions)
        self._save("manual_singletons.json", self.manual_singletons)
        self._save("static_utils.json", self.static_utils)
        self._save("jndi_lookups.json", self.jndi_lookups)
        self._save("dao_service_candidates.json", self.manual_daos)

    def _save(self, filename, data):
        with open(os.path.join(self.output_path, filename), "w") as f:
            json.dump(data, f, indent=2)
