def load_simple_config(file_path):
    config = {}
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):  # 忽略注释和空行
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    return config