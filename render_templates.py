#!/usr/bin/env python3

from shutil import copytree, rmtree
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
                "name": "main",
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
                "name": "main",
                "machine_learning_provider": None,
                "render_name": False,
            },
        ],
        "name": "noml",
        "machine_learning": False,
    },
]
dockerfile_template_name = "Dockerfile.j2"
output_dir = os.getcwd()
templates_dir = os.path.join(output_dir, "templates")


env = Environment(loader=FileSystemLoader(templates_dir))
dockerfile_template = env.get_template(dockerfile_template_name)


for i, flavor in enumerate(flavors):
    print(f"generating Dockerfiles for {flavor['name']}: ")

    type_folder = os.path.join(output_dir, f"build-{flavor['name']}")

    subfolders = [
        os.path.basename(f.path) for f in os.scandir(templates_dir) if f.is_dir()
    ]

    for type in flavor["types"]:
        flavor_folder = os.path.join(type_folder, type["name"])
        root_folder = os.path.join(flavor_folder, "root")

        if os.path.exists(flavor_folder):
            rmtree(flavor_folder)
        os.makedirs(flavor_folder)

        variables = {
            "gpu_acceleration_name": type["machine_learning_provider"],
            "machine_learning": flavor["machine_learning"],
        }

        dockerfile_rendered_template = dockerfile_template.render(variables)
        dockerfile_filepath = os.path.join(flavor_folder, "Dockerfile")

        with open(dockerfile_filepath, "w") as dockerfile:
            dockerfile.write(dockerfile_rendered_template)

        print(f" - Dockerfile for {type['name']} generated successfully.")

        copytree(os.path.join(output_dir, "root"), root_folder)

        for subfolder in subfolders:
            folder_name = os.path.basename(subfolder)
            if not (
                flavor["machine_learning"] is False
                and "machine-learning" in folder_name
            ):
                init_config_template_name = os.path.join(subfolder, "run.j2")
                init_config_template = env.get_template(init_config_template_name)
                init_config_rendered_template = init_config_template.render(variables)

                folder_dir = os.path.join(
                    os.path.join(root_folder, "etc/s6-overlay/s6-rc.d"), folder_name
                )
                run_filepath = os.path.join(folder_dir, "run")

                with open(run_filepath, "w") as run:
                    run.write(init_config_rendered_template)
                    st = os.stat(run_filepath)
                    os.chmod(run_filepath, st.st_mode | 0o111)

    if flavor["machine_learning"] is False:
        rmtree(os.path.join(root_folder, "etc/s6-overlay/s6-rc.d/svc-machine-learning"))
        os.remove(
            os.path.join(
                root_folder,
                "etc/s6-overlay/s6-rc.d/user/contents.d/svc-machine-learning",
            )
        )

    if i < len(flavors) - 1:
        print("")
