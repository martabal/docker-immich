#!/usr/bin/env python3

import argparse
from jinja2 import Environment, FileSystemLoader
import os
from shutil import copytree, rmtree
from typing import List, Tuple, TypedDict, Optional


class Flavor(TypedDict):
    name: str
    machine_learning_provider: Optional[str]


class Group(TypedDict):
    flavors: List[Flavor]
    name: str
    machine_learning: bool


flavors: List[Group] = [
    {
        "flavors": [
            {
                "name": "cuda",
                "machine_learning_provider": "cuda",
            },
            {
                "name": "openvino",
                "machine_learning_provider": "openvino",
            },
            {
                "name": "classic",
                "machine_learning_provider": "cpu",
            },
        ],
        "name": "main",
        "machine_learning": True,
    },
    {
        "flavors": [
            {
                "name": "classic",
                "machine_learning_provider": None,
            },
        ],
        "name": "noml",
        "machine_learning": False,
    },
]
dockerfile_template_name: str = "Dockerfile.j2"
output_dir: str = os.getcwd()
templates_dir: str = os.path.join(output_dir, "templates")

env = Environment(loader=FileSystemLoader(templates_dir))
dockerfile_template = env.get_template(dockerfile_template_name)

subfolders_templates_run: List[str] = [
    os.path.basename(f.path) for f in os.scandir(templates_dir) if f.is_dir()
]


def get_group_and_flavor(
    group_name: str, flavor_name: str
) -> Optional[Tuple[Group, Flavor]]:
    for flavor in flavors:
        if flavor["name"] == group_name:
            for flavor_group in flavor["flavors"]:
                if flavor_group["name"] == flavor_name:
                    return flavor_group, flavor
    return None


def get_flavor_choices() -> List[str]:
    choices = set()
    for flavor in flavors:
        for flavor_group in flavor["flavors"]:
            choices.add(flavor_group["name"])
    return list(choices)


def generate_all() -> None:
    for i, flavor in enumerate(flavors):
        print(f"generating Dockerfiles and context for {flavor['name']}: ")

        group_folder = os.path.join(output_dir, f"build-{flavor['name']}")

        for group in flavor["flavors"]:
            generate_template(
                group["name"],
                group_folder,
                group["machine_learning_provider"],
                flavor["machine_learning"],
            )

        if i < len(flavors) - 1:
            print("")


def generate_template(
    group_name: str,
    group_folder: str,
    group_machine_learning_provider: str,
    flavor_machine_learning: str,
) -> None:
    flavor_folder = os.path.join(group_folder, group_name)
    flavor_root_folder = os.path.join(flavor_folder, "root")
    dockerfile_filepath = os.path.join(flavor_folder, "Dockerfile")

    if not os.path.exists(flavor_folder):
        os.makedirs(flavor_folder)

    if os.path.exists(flavor_root_folder):
        rmtree(flavor_root_folder)

    if os.path.exists(dockerfile_filepath):
        os.remove(dockerfile_filepath)

    variables = {
        "gpu_acceleration_name": group_machine_learning_provider,
        "machine_learning": flavor_machine_learning,
    }

    dockerfile_rendered_template = dockerfile_template.render(variables)

    with open(dockerfile_filepath, "w") as dockerfile:
        dockerfile.write(dockerfile_rendered_template)

    copytree(os.path.join(output_dir, "root"), flavor_root_folder)

    for subfolder in subfolders_templates_run:
        folder_name = os.path.basename(subfolder)
        if not (flavor_machine_learning is False and "machine-learning" in folder_name):
            init_config_template_name: str = os.path.join(subfolder, "run.j2")
            init_config_template = env.get_template(init_config_template_name)
            init_config_rendered_template: str = init_config_template.render(variables)

            folder_dir_path: str = os.path.join(
                os.path.join(flavor_root_folder, "etc/s6-overlay/s6-rc.d"),
                folder_name,
            )
            run_filepath: str = os.path.join(folder_dir_path, "run")

            with open(run_filepath, "w") as run:
                run.write(init_config_rendered_template)
                st = os.stat(run_filepath)
                os.chmod(run_filepath, st.st_mode | 0o111)
        if flavor_machine_learning is False and "machine-learning" in folder_name:
            rmtree(
                os.path.join(
                    flavor_root_folder, "etc/s6-overlay/s6-rc.d/svc-machine-learning"
                )
            )
            os.remove(
                os.path.join(
                    flavor_root_folder,
                    "etc/s6-overlay/s6-rc.d/user/contents.d/svc-machine-learning",
                )
            )
    print(f" - Dockerfile and context for {group_name} generated successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Example program with optional arguments"
    )
    parser.add_argument(
        "-g",
        "--group",
        help="Specify the group",
        type=str,
        choices=[flavor["name"] for flavor in flavors],
    )
    parser.add_argument(
        "-f",
        "--flavor",
        help="Specify the flavor",
        type=str,
        choices=get_flavor_choices(),
    )

    args = parser.parse_args()

    if args.group is not None and args.flavor is not None:
        group_flavor_info = get_group_and_flavor(args.group, args.flavor)
        if group_flavor_info:
            flavor_group, flavor = group_flavor_info
            group_folder = os.path.join(output_dir, f"build-{flavor['name']}")
            print(f"generating Dockerfiles and context for {args.group}: ")
            generate_template(
                flavor_group["name"],
                group_folder,
                flavor_group["name"],
                flavor["machine_learning"],
            )
        else:
            print(f"Can't generate templates for {args.group} - {args.flavor}")
            exit(1)
    elif args.group is None and args.flavor is None:
        generate_all()
    else:
        print(
            f"Please provide a {'group' if args.group is None else 'flavor'}; you need to provide both --group and --flavor arguments"
        )
        exit(1)


if __name__ == "__main__":
    main()
