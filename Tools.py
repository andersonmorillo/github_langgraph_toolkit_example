# %%
from dotenv import load_dotenv
import os
import getpass
from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
from langchain_community.utilities.github import GitHubAPIWrapper
from langgraph.prebuilt import create_react_agent
import getpass
import os
from langchain.chat_models import init_chat_model
from PIL import Image
from langchain_core.tools import Tool
from github import Github


load_dotenv(dotenv_path=".env")  # or use full path if it's not in the same directory
with open("./key.pem", "r") as file:
    private_key = file.read()

os.environ["GITHUB_APP_PRIVATE_KEY"] = private_key


# Optional: confirm the variables are loaded
print(os.getenv("GITHUB_APP_ID"))
print(os.getenv("GITHUB_APP_PRIVATE_KEY"))
print(os.getenv("GITHUB_REPOSITORY"))
print(os.getenv("GOOGLE_API_KEY"))


# For Google Gemini
if not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter API key for Google Gemini: ")


github = GitHubAPIWrapper()
toolkit = GitHubToolkit.from_github_api_wrapper(github)

# Print all available tools in the toolkit
print("Available GitHub tools:")
all_tools = toolkit.get_tools()
for tool in all_tools:
    print(f"- {tool.name}")


# Choose one model:
llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
# llm = init_chat_model("claude-3-5-sonnet-latest", model_provider="anthropic")

# Define image loading function
def _load_image(image_path: str):
    """
    Load an image from the specified path.
    """
    try:
        img = Image.open(image_path)
        return img
    except Exception as e:
        return f"Error loading image: {e}"

# %%

# Create a proper Tool instance
load_image_tool = Tool(
    name="load_image",
    description="Load an image from the specified path from the local host",
    func=_load_image,
)

def upload_image_to_g(file_path):
    """
    Upload an image file to a GitHub repository.
    
    Args:
        file_path: Path to the image file to upload
    
    Returns:
        Success message or error message
    """
    # Default values
    branch = "dev"
    commit_message = "Upload image"
    repository = "andersonmorillo/andersonmorillo.github.io"
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"
            
        # Get GitHub token from environment variable
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            return "Error: GitHub token not found. Set GITHUB_TOKEN environment variable."
            
        # Initialize GitHub client
        g = Github(github_token)
        repo = g.get_repo(repository)
        
        # Read image file
        with open(file_path, "rb") as f:
            file_content = f.read()
            
        # Get filename from path
        file_name = os.path.basename(file_path)
        
        # Check if file already exists in repo
        file_exists = False
        file_sha = None
        try:
            contents = repo.get_contents(file_name, ref=branch)
            file_exists = True
            file_sha = contents.sha
        except Exception:
            pass
            
        # Upload file
        if file_exists:
            result = repo.update_file(
                path=file_name,
                message=commit_message,
                content=file_content,
                sha=file_sha,
                branch=branch
            )
            return f"Updated image at {result['content'].html_url}"
        else:
            result = repo.create_file(
                path=file_name,
                message=commit_message,
                content=file_content,
                branch=branch
            )
            return f"Created image at {result['content'].html_url}"
            
    except Exception as e:
        return f"Error uploading image: {str(e)}"

# Create tool for uploading images to GitHub
push_image_tool = Tool(
    name="push_image_to_g",
    description="Upload an image from local host to a GitHub repository",
    func=upload_image_to_g,
)

# Select the tools we want by name
wanted_tool_names = [
    "Read File",
    "Get files from a directory",
    "Create File",
    "Update File",
    "Delete File",
    "Overview of existing files in Main branch",
    "List branches in this repository",
    "Set active branch",
    "Create a new branch",
    "Create Pull Request",
    "List open pull requests (PRs)",
]
tools = [tool for tool in all_tools if tool.name in wanted_tool_names] + [load_image_tool, push_image_tool]

# Print the selected tools
print(f"\nSelected {len(tools)} tools:")
for tool in tools:
    # Store original name
    original_name = tool.name

    # Replace spaces with underscores for compatibility
    new_name = original_name.replace(" ", "_")
    new_name = new_name.replace("(", "")
    new_name = new_name.replace(")", "")

    # Update the tool name
    tool.name = new_name
    print(f"- {tool.name}")

# Create the agent with selected tools
agent_executor = create_react_agent(llm, tools)

# %%
# Test the original query
# print("\n=== Testing original query ===")
# example_query = "read the ./image.png from the local and upload the image to the github repository"

# events = agent_executor.stream(
#     {"messages": [("user", example_query)]},
#     stream_mode="values",
# )
# for event in events:
#     event["messages"][-1].pretty_print()

#%%
# from github import Github

# def push_image_loader(file_path: str = "./image.png", branch: str= "dev", commit_message:str = "", repository:str = "andersonmorillo/andersonmorillo.github.io"):
#     g=Github("Git Token")
#     repo=g.get_repo("Repo")
#     with open(file_path, "rb") as image:
#         f = image.read()
#         image_data = bytearray(f)


#     def push_image(path,commit_message,content,branch,update=False):
#         if update:
#             contents = repo.get_contents(path, ref=branch)
#             repo.update_file(contents.path, commit_message, content, sha=contents.sha, branch)
#         else:
#             repo.create_file(path, commit_message, content, branch)


#     push_image (file_path,message, bytes(image_data), branch, update=False)



# # %%
# # Test the branch and branch-related tools
# print("\n=== Testing branch-related tools ===")
# branch_query = "List all branches in this repository"

# branch_events = agent_executor.stream(
#     {"messages": [("user", branch_query)]},
#     stream_mode="values",
# )
# for event in branch_events:
#     event["messages"][-1].pretty_print()

# %%
# Use case: Update _config.yml with resume information by creating a new branch and PR
print("\n=== Updating _config.yml with resume information ===")
update_query = """
Then, read the from the dev file _config.yml from path ./_config.yml and update it with the following information:
- name: Anderson Morillo
- title: Python Developer and NLP Researcher
- email: amorillo@utb.edu.co
- location: Cartagena de indias, Bolívar, Colombia
- description: Research assistant at VerbaNex AI Lab specializing in NLP with experience in sentiment analysis, text summarization, and machine translation.
- github: andersonmorillo
- linkedin: anderson-morillo-792515153
Finally, create a pull request to merge these changes into the main branch with the title "Update _config.yml with Anderson Morillo's information"
# """

update_events = agent_executor.stream(
    {"messages": [("user", update_query)]},
    stream_mode="values",
)
for event in update_events:
    event["messages"][-1].pretty_print()

# %%
# Verify the tool names
print("\nTool names after setup:")
for tool in tools:
    print(f"- {tool.name}")

# %%
