import os
import subprocess


def generate_documentation():
    # Get the absolute path of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Define absolute paths to the source code directories
    main_dir = os.path.join(script_dir, '..', 'main')
    modules_dir = os.path.join(script_dir, '..', 'modules')
    routes_dir = os.path.join(script_dir, '..', 'routes')

    # Check and create docs folder if missing
    docs_dir = os.path.abspath(os.path.join(script_dir, '..', 'docs'))
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)

    # Create or overwrite conf.py
    conf_py_path = os.path.join(docs_dir, 'conf.py')
    conf_py_content = (
        "# Configuration file for the Sphinx documentation builder.\n"
        "import os\n"
        "import sys\n"
        "\n"
        f"project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))\n"
        "sys.path.insert(0, project_root)\n"
        "\n"
        "extensions = [\n"
        "    'autoapi.extension',\n"  # Add autoapi extension
        "    # ... Other extensions ...\n"
        "]\n"
        "\n"
        "# AutoAPI settings\n"
        f"autoapi_dirs = [\n"
        f"    '{main_dir}',\n"
        f"    '{modules_dir}',\n"
        f"    '{routes_dir}'\n"
        "]\n"
        "autoapi_exclude = ['venv', 'pip', 'django', '__init__.py']  # Exclude venv folder\n"
        "autoapi_file_patterns = ['*.py']\n"
        "\n"
        "# ... Other configuration settings ...\n"
        "html_theme = 'pydata_sphinx_theme'\n"
    )

    with open(conf_py_path, 'w') as conf_py:
        conf_py.write(conf_py_content)

    # Generate autoapi TOC entries
    with open(os.path.join(docs_dir, 'index.rst'), 'w') as index_rst:
        index_rst.write(
            "Welcome to AmethystKey - CRYSTAL Secret Management's documentation!\n"
            "=========================================================================\n\n"
            ".. toctree::\n"
            "   :maxdepth: 2\n"
            "   :caption: Contents:\n\n"
            "   autoapi/index\n"
            ".. toctree::\n"
            "   :maxdepth: 1\n"
            "   :caption: AutoAPI Documentation\n\n"
        )
        for root, _, files in os.walk(os.path.join(docs_dir, '_build', 'autoapi')):
            for file in files:
                if file.endswith(".rst"):
                    rst_path = os.path.relpath(os.path.join(root, file),
                                               os.path.join(docs_dir, '_build', 'autoapi'))
                    index_rst.write(f"   autoapi/{rst_path}\n")

    # Create _build folder inside docs
    build_dir = os.path.join(docs_dir, '_build')
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

    # Run Sphinx build command
    # subprocess.run(['sphinx-build', '-b', 'html', 'docs', '_build'], cwd=os.path.join(script_dir, '..'))
    subprocess.run(['sphinx-build', '-b', 'html', '.', '_build'], cwd=docs_dir)
