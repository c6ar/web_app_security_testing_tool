from pathlib import Path


# ================================================
# App configuration functionality
# ================================================
CONFIG_PATH = Path.cwd().parent / "app.conf"


def update_config(config):
    global RUNNING_CONFIG
    RUNNING_CONFIG = config


def load_config():
    config = DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "r") as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("#"):
                    setting, val = line.split("=", 1)
                    if "#" in val:
                        val, _ = val.split("#", 1)
                    val = val.strip().lower()
                    setting = setting.strip().lower()

                    if setting == "theme":
                        if val not in ("system", "dark", "light"):
                            print("[ERROR] CONFIG: Incorrect value given, where system, dark or light expected.")
                            continue

                    if setting.endswith("port"):
                        try:
                            val = int(val)
                        except ValueError:
                            print("[ERROR] CONFIG: Incorrect value given, where int expected.")
                            continue

                    if setting in ("debug_mode", "proxy_console"):
                        if val not in (1, 0, "1", "0", "true", "false"):
                            print("[ERROR] CONFIG: Incorrect value given, where bool expected (false, true, 0 or 1).")
                            continue

                    if setting in (1, "1", "true"):
                        val = True
                    if val in (0, "0", "false"):
                        val = False

                    config[setting] = val
    except FileNotFoundError:
        print("[ERROR] CONFIG: App config file could not be open. Default settings have been loaded.")
    return config


def save_config(config):
    try:
        with open(CONFIG_PATH, "r") as file:
            lines = file.readlines()

        updated_lines = []
        settings_found = set()
        for line in lines:
            if line.strip() and not line.strip().startswith("#"):
                setting, val = line.split("=", 1)
                setting = setting.strip()
                if setting in config:
                    updated_lines.append(f"{setting} = {config[setting]}\n")
                    settings_found.add(setting)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)

        for setting, val in config.items():
            if setting not in settings_found:
                updated_lines.append(f"{setting} = {val}\n")

        with open(CONFIG_PATH, "w") as file:
            file.writelines(updated_lines)
            load_config()
    except Exception as e:
        print(f"Error during saving a config: {e}")


DEFAULT_CONFIG = {
    "theme": "system",
    "lang": "english",
    "proxy_host_address": "127.0.0.1",
    "proxy_port": 8082,
    "proxy_logging": 1,
    "proxy_logs_location": f"{Path.cwd()}\\proxy_logs",
    "proxy_console": False,
    "front_back_intercept_toggle_port": 65430,
    "back_front_request_to_traffic_port": 65432,
    "back_front_request_to_intercept_port": 65433,
    "front_back_data_port": 65434,
    "front_back_scope_update_port": 65436,
    "debug_mode": False,
    "debug_show_running_config": False
}
RUNNING_CONFIG = load_config()

if Path.cwd().name == "frontend":
    if RUNNING_CONFIG["debug_show_running_config"]:
        print("================================================\n"
              "[DEBUG] Running config: ")
        for config_item, config_value in RUNNING_CONFIG.items():
            print(f"\t{config_item} = {config_value}")
        print("================================================\n")

    if RUNNING_CONFIG["debug_mode"]:
        print("[DEBUG] Debug mode is ON. App will print debug messages to the console.")
    else:
        print("[INFO] Debug mode is OFF. App will print only error and important info messages to the console.")