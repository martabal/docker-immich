#!/usr/bin/env python3

import shutil
from jinja2 import Environment, FileSystemLoader
import os


flavors = [
    {
        "types": [
            {
                "name": "cuda",
                "machine_learning_provider": "cuda",
                "render_name": True,
            },
            {
                "name": "openvino",
                "machine_learning_provider": "openvino",
                "render_name": True,
            },
            {
                "name": "classic",
                "machine_learning_provider": "cpu",
                "render_name": False,
            },
        ],
        "name": "main",
        "machine_learning": True,
    },
    {
        "types": [
            {
                "name": "classic",
                "machine_learning_provider": None,
                "render_name": False,
            },
        ],
        "name": "noml",
        "machine_learning": False,
    },
]
dockerfile_template = "Dockerfile.j2"
init_config_template = "run.j2"
output_dir = os.getcwd()

env = Environment(loader=FileSystemLoader(os.path.join(output_dir, "templates")))
dockerfile_template = env.get_template(dockerfile_template)
init_config_template = env.get_template(init_config_template)

for i, flavor in enumerate(flavors):
    print(f"generating Dockerfiles for {flavor['name']}: ")

    type_folder = os.path.join(output_dir, f"build-{flavor['name']}")
    os.makedirs(type_folder, exist_ok=True)

    for type in flavor["types"]:
        variables = {
            "gpu_acceleration_name": type["machine_learning_provider"],
            "machine_learning": flavor["machine_learning"],
        }
        dockerfile_rendered_template = dockerfile_template.render(variables)

        filename = "Dockerfile"
        if type["render_name"]:
            filename = f"{filename}.{type['name']}"

        dockerfile_filepath = os.path.join(type_folder, filename)

        with open(dockerfile_filepath, "w") as dockerfile:
            dockerfile.write(dockerfile_rendered_template)

        print(f" - {filename} generated successfully.")

    root_folder = os.path.join(type_folder, "root")

    if os.path.exists(root_folder):
        shutil.rmtree(root_folder)

    shutil.copytree(os.path.join(output_dir, "root"), root_folder)

    if flavor["machine_learning"] is False:
        shutil.rmtree(
            os.path.join(root_folder, "etc/s6-overlay/s6-rc.d/svc-machine-learning")
        )
        os.remove(
            os.path.join(
                root_folder,
                "etc/s6-overlay/s6-rc.d/user/contents.d/svc-machine-learning",
            )
        )

    init_config_rendered_template = init_config_template.render(variables)
    run_filepath = os.path.join(
        os.path.join(root_folder, "etc/s6-overlay/s6-rc.d/init-config-immich"), "run"
    )

    with open(run_filepath, "w") as run:
        run.write(init_config_rendered_template)
        st = os.stat(run_filepath)
        os.chmod(run_filepath, st.st_mode | 0o111)

    if i < len(flavors) - 1:
        print("")
