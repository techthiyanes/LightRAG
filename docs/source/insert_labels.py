import os


def add_reference_labels(directory: str):
    for filename in os.listdir(directory):
        if filename.endswith(".rst"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r+") as file:
                content = file.read()
                file.seek(0, 0)
                module_label = filename.replace(".rst", "").replace(".", "-")
                label_line = f".. _{module_label}:\n\n"
                file.write(label_line + content)


if __name__ == "__main__":
    # Specify the directories you want to process
    add_reference_labels("./source/apis/core")
    add_reference_labels("./source/apis/components")