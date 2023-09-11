import os
import subprocess
import logging
from globals import LOG_LEVEL


logging.basicConfig(level=LOG_LEVEL)


def setup_directories(script_dir):
    main_dir = os.path.join(script_dir, '..', 'main')
    modules_dir = os.path.join(script_dir, '..', 'modules')
    routes_dir = os.path.join(script_dir, '..', 'routes')
    docs_dir = os.path.abspath(os.path.join(script_dir, '..', 'docs'))
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)

    return main_dir, modules_dir, routes_dir, docs_dir


def create_conf_py(main_dir, modules_dir, routes_dir, docs_dir):
    conf_py_path = os.path.join(docs_dir, 'conf.py')
    conf_py_content = (
        "# Configuration file for the Sphinx documentation builder.\n"
        "import os\n"
        "import sys\n"
        "\n"
        f"project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))\n"
        "sys.path.insert(0, project_root)\n"
        "\n"
        "extensions = ['autoapi.extension']\n"
        "\n"
        "# AutoAPI settings\n"
        f"autoapi_dirs = ['{main_dir}','{modules_dir}','{routes_dir}']\n"
        "autoapi_exclude = ['venv', 'pip', 'django', '__init__.py']\n"
        "autoapi_file_patterns = ['*.py']\n"
        "\n"
        "html_theme = 'pydata_sphinx_theme'\n"
    )

    with open(conf_py_path, 'w') as conf_py:
        conf_py.write(conf_py_content)
    logging.info(f"Configuration file created at {conf_py_path}")


def generate_autoapi_toc_entries(docs_dir):
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
    logging.info("TOC entries for AutoAPI generated.")


def run_sphinx_build(docs_dir):
    build_dir = os.path.join(docs_dir, '_build')
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
    subprocess.run(['sphinx-build', '-b', 'html', '.', '_build'], cwd=docs_dir)
    logging.info("Sphinx build completed.")


def generate_documentation():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        main_dir, modules_dir, routes_dir, docs_dir = setup_directories(script_dir)
        create_conf_py(main_dir, modules_dir, routes_dir, docs_dir)
        generate_autoapi_toc_entries(docs_dir)
        run_sphinx_build(docs_dir)
        logging.info("Documentation generation completed successfully.")
    except Exception as e:
        logging.error(f"Error generating documentation: {str(e)}")
