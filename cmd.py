# import subprocess

# # Specify the command and its arguments as a list
# command = ["bash", " C:\Code\Work\Flask Scrapping API\cmd.sh"]

# # Run the command
# process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# # Check the result
# if process.returncode == 0:
#     print("Command executed successfully.")
#     print("Output: ", process.stdout)
# else:
#     print("Error executing the command.")
#     print("Error output: ", process.stderr)




import subprocess
import sys

# Get the full path to the Python executable
python_executable = sys.executable

# Specify the full path to the Scrapy script
scrapy_script = r"C:\path\to\scrapy"  # Replace with the actual path to your scrapy script

# Specify the command and its arguments as a list
command = [python_executable, scrapy_script, "crawl", "indeed_jobs", "-o", "outputcmd.json", "-a", "keyword=C++", "-a", "location=New York"]

# Run the command
process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# Check the result
if process.returncode == 0:
    print("Command executed successfully.")
    print("Output: ", process.stdout)
else:
    print("Error executing the command.")
    print("Error output: ", process.stderr)
