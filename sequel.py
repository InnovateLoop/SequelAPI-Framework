import os
import shutil
import click
import isort
import ast

@click.group()
def cli():
    pass

@cli.command()
def build():
    """Convert the project into an encapsulated FastAPI codebase."""
    lib_dir = 'lib'
    src_dir = 'src'
    src_dir_api = os.path.join(src_dir, 'api')
    models_dir = os.path.join(src_dir, 'models', 'beanie')
    dockerfile_dir = os.path.join('.', 'Dockerfile')
    requirements_dir = os.path.join(src_dir, 'requirements.txt')

    dest_dir_root = 'dist'
    dest_dir_src = os.path.join(dest_dir_root, 'src')
    dest_dir_sequel = os.path.join(dest_dir_src, 'sequel')

    if os.path.exists(dest_dir_root):
        shutil.rmtree(dest_dir_root)
    os.makedirs(dest_dir_root)
    
    shutil.copy(dockerfile_dir, dest_dir_root)
    shutil.copy(requirements_dir, dest_dir_root)
    shutil.copytree(lib_dir, dest_dir_sequel)

    imports = []
    routes = []
    model_imports = []
    model_names = []

    def sanitize_name(name):
        """Sanitize filenames and module names by replacing invalid characters."""
        return name.replace('[', '_').replace(']', '_').replace('-', '_').replace(' ', '_')

    def is_beanie_document(file_path):
        """Check if the file contains a class inheriting from beanie.Document."""
        with open(file_path, 'r') as file:
            tree = ast.parse(file.read(), filename=file_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name):
                            if base.attr == 'Document' and base.value.id == 'beanie':
                                return node.name
                        elif isinstance(base, ast.Name) and base.id == 'Document':
                            if check_imports_for_beanie(file_path, base.id):
                                return node.name
        return None

    def check_imports_for_beanie(file_path, base_name):
        """Trace imports to determine if the base class is beanie.Document."""
        with open(file_path, 'r') as file:
            tree = ast.parse(file.read(), filename=file_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module == 'beanie' and base_name in [alias.name for alias in node.names]:
                        return True
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == 'beanie':
                            return True
        return None

    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                relative_path = os.path.relpath(os.path.join(root, file), src_dir)
                sanitized_relative_path = os.path.join(
                    *[sanitize_name(part) for part in relative_path.split(os.sep)]
                )
                module_path = sanitized_relative_path.replace('.py', '').replace(os.sep, '.')
                dest_path = os.path.join(dest_dir_src, sanitized_relative_path)

                if '/models/beanie' in root:
                    model_name = is_beanie_document(os.path.join(root, file))
                    if model_name:
                        model_imports.append(f"from {module_path} import {model_name}\n")
                        model_names.append(model_name)
    
                if '/api' in root and relative_path.endswith(os.path.join(os.sep, 'route.py')):
                    route_path = relative_path.replace('[', '{').replace(']', '}').replace(os.sep, '/').replace('route.py', '').rstrip("/")
                    
                    imports.append(f"from {module_path} import router as {module_path.replace('.', '_')}_router\n")
                    routes.append(f"app.include_router({module_path.replace('.', '_')}_router, prefix='/{route_path}')\n")

                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy(os.path.join(root, file), dest_path)

    # Writing to the main.py file
    with open(os.path.join(dest_dir_src, 'main.py'), 'w') as main_file:
        main_file.writelines(
            [
                "from fastapi import FastAPI\n",
                "from fastapi.middleware.gzip import GZipMiddleware\n",
                "from sequel.metering.openmeter import CloudEventMetering\n",
                "import os\n",
                 "from sequel.auth.clerk import ClerkBearerAuthProvider\n"
            ] +
            
            (
                [
                    "from beanie import init_beanie\n",
                    "from motor.motor_asyncio import AsyncIOMotorClient\n" 
                ] if model_names else []
            ) +

            imports +
               (model_imports if model_names else [])+
            [
                "auth_provider = ClerkBearerAuthProvider()\n"
            ] +
            (
                [
                    "async def lifespan(app: FastAPI):\n", 
                        "    asyncio_motor_client = AsyncIOMotorClient(os.environ[\"MONGODB_CONN_STRING\"])\n", 
                        "    auth_provider.init()\n",
                        "    await init_beanie(database=asyncio_motor_client.get_default_database(), document_models=[\n"
                    ] + [
                        f"        {model_name},\n" for model_name in model_names
                    ] + [
                        "    ])\n",
                        "\n",
                        "    yield\n\n"
                ] if model_names else []
            ) +

            [
                "\n",
                "app = FastAPI(" +
                    ("lifespan=lifespan, " if model_names else "") +
                    "dependencies=[auth_provider.require_user()]" +
                ")\n",
                "app.add_middleware(GZipMiddleware)\n",
                "app.add_middleware(CloudEventMetering)\n",
                "\n"
            ] +

            routes
        )

    # Sort imports in main.py quietly
    isort.file(os.path.join(dest_dir_src, 'main.py'), quiet=True)

if __name__ == '__main__':
    cli()
