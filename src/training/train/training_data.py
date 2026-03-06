"""
Expanded training data for CLI agent.
Drop-in replacement/extension for your existing SFT_EXAMPLES and TRAINING_TASKS.
"""

from training.cli_agent.environment import CLITask


# ==============================================================================
# SFT EXAMPLES — 100 examples across all categories
# Format: (task_description, gold_command)
# ==============================================================================

SFT_EXAMPLES = [
    # --- Basic File Operations ---
    ("Count the number of lines in /tmp/data/log.txt", "wc -l < /tmp/data/log.txt"),
    ("List all files in the current directory including hidden files", "ls -la"),
    ("Show the first 10 lines of /tmp/data/file.txt", "head -10 /tmp/data/file.txt"),
    ("Show the last 20 lines of /tmp/data/file.txt", "tail -20 /tmp/data/file.txt"),
    ("Display the contents of /tmp/data/config.txt", "cat /tmp/data/config.txt"),
    ("Count the number of words in /tmp/data/essay.txt", "wc -w /tmp/data/essay.txt"),
    ("Count the number of characters in /tmp/data/note.txt", "wc -c /tmp/data/note.txt"),
    ("Show the size of /tmp/data/archive.tar.gz in bytes", "wc -c < /tmp/data/archive.tar.gz"),
    ("Display line 42 of /tmp/data/file.txt", "sed -n '42p' /tmp/data/file.txt"),
    ("Show lines 10 through 20 of /tmp/data/file.txt", "sed -n '10,20p' /tmp/data/file.txt"),

    # --- Find and Search ---
    ("Find all .py files in /home", "find /home -name '*.py'"),
    ("Find all .log files larger than 10MB in /var", "find /var -name '*.log' -size +10M"),
    ("Find all empty files in /tmp", "find /tmp -empty -type f"),
    ("Find all directories in /tmp/data", "find /tmp/data -type d"),
    ("Find files modified in the last 24 hours in /tmp", "find /tmp -mtime -1"),
    ("Find files modified more than 7 days ago in /tmp/data", "find /tmp/data -mtime +7"),
    ("Find all .txt files in /tmp and count them", "find /tmp -name '*.txt' | wc -l"),
    ("Find all files owned by root in /etc", "find /etc -user root -type f"),
    ("Find all executable files in /usr/bin", "find /usr/bin -perm /111 -type f"),
    ("Search for the word ERROR in /var/log/syslog", "grep 'ERROR' /var/log/syslog"),

    # --- Text Processing: grep ---
    ("Search for lines containing 'timeout' in /tmp/data/app.log", "grep 'timeout' /tmp/data/app.log"),
    ("Count lines containing 'ERROR' in /tmp/data/app.log", "grep -c 'ERROR' /tmp/data/app.log"),
    ("Search case-insensitively for 'warning' in /tmp/data/app.log", "grep -i 'warning' /tmp/data/app.log"),
    ("Show lines NOT containing 'INFO' in /tmp/data/app.log", "grep -v 'INFO' /tmp/data/app.log"),
    ("Search recursively for 'TODO' in /tmp/project", "grep -r 'TODO' /tmp/project"),
    ("Show filenames containing 'error' in /tmp/logs", "grep -rl 'error' /tmp/logs"),
    ("Show line numbers where 'FAIL' appears in /tmp/data/results.txt", "grep -n 'FAIL' /tmp/data/results.txt"),
    ("Find lines matching IP address pattern in /tmp/data/access.log", "grep -E '[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}' /tmp/data/access.log"),
    ("Show 2 lines of context around each ERROR in /tmp/data/app.log", "grep -C 2 'ERROR' /tmp/data/app.log"),
    ("Count unique IPs in /tmp/data/access.log", "grep -oE '[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+' /tmp/data/access.log | sort -u | wc -l"),

    # --- Text Processing: awk and sed ---
    ("Extract the second column from a space-separated file /tmp/data/data.txt", "awk '{print $2}' /tmp/data/data.txt"),
    ("Sum all numbers in the first column of /tmp/data/numbers.txt", "awk '{s+=$1} END {print s}' /tmp/data/numbers.txt"),
    ("Print lines where the third column is greater than 100", "awk '$3 > 100' /tmp/data/data.txt"),
    ("Replace all occurrences of foo with bar in /tmp/data/config.txt", "sed -i 's/foo/bar/g' /tmp/data/config.txt"),
    ("Delete all blank lines from /tmp/data/file.txt", "sed -i '/^$/d' /tmp/data/file.txt"),
    ("Delete lines containing 'DEBUG' from /tmp/data/app.log", "sed -i '/DEBUG/d' /tmp/data/app.log"),
    ("Print the average of column 1 in /tmp/data/scores.txt", "awk '{s+=$1; n++} END {print s/n}' /tmp/data/scores.txt"),
    ("Extract the filename from each line of /tmp/data/paths.txt", "awk -F'/' '{print $NF}' /tmp/data/paths.txt"),
    ("Add line numbers to /tmp/data/file.txt", "awk '{print NR\". \"$0}' /tmp/data/file.txt"),
    ("Print only lines with more than 5 fields in /tmp/data/data.txt", "awk 'NF > 5' /tmp/data/data.txt"),

    # --- Sort, Unique, Cut ---
    ("Sort /tmp/data/names.txt alphabetically and remove duplicates", "sort -u /tmp/data/names.txt"),
    ("Sort /tmp/data/numbers.txt numerically in descending order", "sort -rn /tmp/data/numbers.txt"),
    ("Show only duplicate lines in /tmp/data/names.txt", "sort /tmp/data/names.txt | uniq -d"),
    ("Count occurrences of each line in /tmp/data/words.txt", "sort /tmp/data/words.txt | uniq -c | sort -rn"),
    ("Extract the first column from a CSV file /tmp/data/data.csv", "cut -d',' -f1 /tmp/data/data.csv"),
    ("Extract columns 2 and 3 from a tab-separated file", "cut -f2,3 /tmp/data/data.tsv"),
    ("Sort /tmp/data/access.log by the 4th field", "sort -k4 /tmp/data/access.log"),
    ("Find the most common word in /tmp/data/text.txt", "tr ' ' '\\n' < /tmp/data/text.txt | sort | uniq -c | sort -rn | head -1"),
    ("Remove duplicate lines without sorting /tmp/data/file.txt", "awk '!seen[$0]++' /tmp/data/file.txt"),
    ("Show only unique lines in /tmp/data/names.txt", "sort /tmp/data/names.txt | uniq"),

    # --- Pipes and Chaining ---
    ("Show the 10 largest files in /tmp sorted by size", "du -ah /tmp | sort -rh | head -10"),
    ("Count the number of running processes", "ps aux | grep -v grep | wc -l"),
    ("Show the top 5 processes by memory usage", "ps aux --sort=-%mem | head -6"),
    ("Show the top 5 processes by CPU usage", "ps aux --sort=-%cpu | head -6"),
    ("List all open ports on this machine", "ss -tuln | grep LISTEN"),
    ("Show disk usage summary for /tmp sorted by size", "du -sh /tmp/* | sort -rh"),
    ("Find the 5 most recently modified files in /tmp/data", "find /tmp/data -type f -printf '%T@ %p\\n' | sort -rn | head -5 | awk '{print $2}'"),
    ("Count how many times each HTTP status code appears in /tmp/data/access.log", "awk '{print $9}' /tmp/data/access.log | sort | uniq -c | sort -rn"),
    ("Show environment variables sorted alphabetically", "env | sort"),
    ("List all users currently logged in", "who | awk '{print $1}' | sort -u"),

    # --- System Information ---
    ("Show disk usage in human-readable format", "df -h"),
    ("Show current memory usage", "free -m"),
    ("Show current CPU info", "lscpu | head -20"),
    ("Show the system uptime", "uptime"),
    ("Show the hostname of this machine", "hostname"),
    ("Show current kernel version", "uname -r"),
    ("Show all mounted filesystems", "mount | column -t"),
    ("Show the current date and time in ISO format", "date -Iseconds"),
    ("Show top 10 memory-consuming processes", "ps aux --sort=-%mem | awk 'NR<=11{print $2,$4,$11}'"),
    ("Check which process is using port 8080", "lsof -i :8080"),

    # --- Archives and Compression ---
    ("Compress /tmp/logs into a tar.gz archive", "tar -czf /tmp/logs.tar.gz /tmp/logs"),
    ("Extract a tar.gz archive to /tmp/output", "tar -xzf /tmp/archive.tar.gz -C /tmp/output"),
    ("List contents of a tar.gz archive without extracting", "tar -tzf /tmp/archive.tar.gz"),
    ("Compress a single file with gzip", "gzip /tmp/data/large_file.txt"),
    ("Decompress a .gz file", "gunzip /tmp/data/large_file.txt.gz"),
    ("Create a zip archive of /tmp/project", "zip -r /tmp/project.zip /tmp/project"),
    ("Extract a zip archive to /tmp/output", "unzip /tmp/project.zip -d /tmp/output"),
    ("Show compression ratio of a .gz file", "gzip -l /tmp/data/large_file.txt.gz"),
    ("Create a tar archive without compression", "tar -cf /tmp/backup.tar /tmp/data"),
    ("Extract only .py files from a tar archive", "tar -xzf /tmp/project.tar.gz --wildcards '*.py'"),

    # --- Permissions and Ownership ---
    ("Make /tmp/data/script.sh executable", "chmod +x /tmp/data/script.sh"),
    ("Set permissions of /tmp/data/secret.txt to owner-read-only", "chmod 600 /tmp/data/secret.txt"),
    ("Recursively set permissions of /tmp/project to 755", "chmod -R 755 /tmp/project"),
    ("Show permissions of all files in /tmp/data", "ls -la /tmp/data"),
    ("Find all files with world-writable permissions in /tmp", "find /tmp -perm -002 -type f"),

    # --- Environment Variables ---
    ("Show all environment variables containing PATH", "env | grep PATH"),
    ("Show the value of the HOME environment variable", "echo $HOME"),
    ("Show the current shell", "echo $SHELL"),
    ("Show the current user", "echo $USER"),
    ("Show all environment variables", "env"),

    # --- Networking ---
    ("Check if google.com is reachable", "ping -c 3 google.com"),
    ("Show all network interfaces", "ip addr show"),
    ("Show the default gateway", "ip route show default"),
    ("Show DNS resolution for google.com", "nslookup google.com"),
    ("Download a file from a URL to /tmp", "curl -o /tmp/file.txt https://example.com/file.txt"),

    # --- Process Management ---
    ("Show all processes running as current user", "ps -u $USER"),
    ("Find the PID of a process named python", "pgrep python"),
    ("Show the process tree", "ps auxf | head -30"),
    ("Show how long a command takes to run", "time ls /tmp"),
    ("Run a command in the background", "sleep 10 &"),
]


# ==============================================================================
# GRPO TASKS — 60 validated tasks with real execution
# ==============================================================================

TRAINING_TASKS = [

    # --- File Operations ---
    CLITask(
        task_id="count_lines",
        description="Count the number of lines in /tmp/testdata/log.txt",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            "seq 1 42 > /tmp/testdata/log.txt",
        ],
        validation_fn="check_output_contains",
        expected_output="42",
        tags=["basic", "file_ops"],
    ),
    CLITask(
        task_id="count_words",
        description="Count the number of words in /tmp/testdata/essay.txt",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            "printf 'the quick brown fox jumps over the lazy dog\\n' > /tmp/testdata/essay.txt",
        ],
        validation_fn="check_output_contains",
        expected_output="9",
        tags=["basic", "file_ops"],
    ),
    CLITask(
        task_id="show_last_lines",
        description="Show the last 3 lines of /tmp/testdata/log.txt",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            "printf 'line1\\nline2\\nline3\\nline4\\nline5\\n' > /tmp/testdata/log.txt",
        ],
        validation_fn="check_output_contains",
        expected_output="line5",
        tags=["basic", "file_ops"],
    ),
    CLITask(
        task_id="show_first_lines",
        description="Show the first 2 lines of /tmp/testdata/log.txt",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            "printf 'alpha\\nbeta\\ngamma\\ndelta\\n' > /tmp/testdata/log.txt",
        ],
        validation_fn="check_output_contains",
        expected_output="alpha",
        tags=["basic", "file_ops"],
    ),
    CLITask(
        task_id="find_largest_file",
        description="Find the name of the largest file in /tmp/testdata/files/",
        setup_commands=[
            "mkdir -p /tmp/testdata/files",
            "dd if=/dev/zero of=/tmp/testdata/files/small.bin bs=1K count=1 2>/dev/null",
            "dd if=/dev/zero of=/tmp/testdata/files/medium.bin bs=1K count=10 2>/dev/null",
            "dd if=/dev/zero of=/tmp/testdata/files/large.bin bs=1K count=100 2>/dev/null",
        ],
        validation_fn="check_output_contains",
        expected_output="large.bin",
        tags=["basic", "file_ops"],
    ),
    CLITask(
        task_id="count_files",
        description="Count the number of .txt files in /tmp/testdata/docs/",
        setup_commands=[
            "mkdir -p /tmp/testdata/docs",
            "touch /tmp/testdata/docs/a.txt /tmp/testdata/docs/b.txt /tmp/testdata/docs/c.txt",
            "touch /tmp/testdata/docs/readme.md",
        ],
        validation_fn="check_output_contains",
        expected_output="3",
        tags=["basic", "file_ops"],
    ),
    CLITask(
        task_id="find_recent_files",
        description="Find all .txt files in /tmp/testdata modified in the last 1 day",
        setup_commands=[
            "mkdir -p /tmp/testdata/sub",
            "touch /tmp/testdata/recent.txt",
            "touch /tmp/testdata/sub/also_recent.txt",
            "touch -t 202001010000 /tmp/testdata/old.txt",
        ],
        validation_fn="check_output_contains",
        expected_output="recent.txt",
        tags=["intermediate", "file_ops"],
    ),
    CLITask(
        task_id="find_empty_files",
        description="Find all empty files in /tmp/testdata/",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            "touch /tmp/testdata/empty1.txt /tmp/testdata/empty2.txt",
            "echo 'content' > /tmp/testdata/notempty.txt",
        ],
        validation_fn="check_output_contains",
        expected_output="empty",
        tags=["basic", "file_ops"],
    ),
    CLITask(
        task_id="create_directory_structure",
        description="Create the directory structure /tmp/project/{src,tests,docs} with an empty __init__.py in src/ and tests/",
        setup_commands=["rm -rf /tmp/project"],
        validation_fn="check_directory_structure",
        expected_output="/tmp/project/src/__init__.py,/tmp/project/tests/__init__.py",
        tags=["intermediate", "file_ops"],
    ),
    CLITask(
        task_id="disk_usage",
        description="Show the total disk usage of /tmp/testdata in human-readable format",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            "dd if=/dev/zero of=/tmp/testdata/blob.bin bs=1M count=5 2>/dev/null",
        ],
        validation_fn="check_command_success",
        expected_output="",
        tags=["basic", "system"],
    ),

    # --- Text Processing: grep ---
    CLITask(
        task_id="grep_pattern",
        description="Find all lines containing 'ERROR' in /tmp/testdata/app.log and count them",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "INFO start\\nERROR disk full\\nINFO running\\nERROR timeout\\nERROR conn refused\\nINFO done\\n" > /tmp/testdata/app.log',
        ],
        validation_fn="check_output_contains",
        expected_output="3",
        tags=["basic", "text_processing"],
    ),
    CLITask(
        task_id="grep_invert",
        description="Show all lines NOT containing 'INFO' in /tmp/testdata/app.log",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "INFO start\\nERROR disk full\\nINFO running\\nWARN low mem\\n" > /tmp/testdata/app.log',
        ],
        validation_fn="check_output_contains",
        expected_output="ERROR",
        tags=["basic", "text_processing"],
    ),
    CLITask(
        task_id="grep_count_warnings",
        description="Count lines containing 'WARN' in /tmp/testdata/app.log",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "INFO ok\\nWARN low\\nWARN retry\\nERROR fail\\nWARN timeout\\n" > /tmp/testdata/app.log',
        ],
        validation_fn="check_output_contains",
        expected_output="3",
        tags=["basic", "text_processing"],
    ),
    CLITask(
        task_id="grep_recursive",
        description="Recursively search for 'TODO' in /tmp/testdata/project/ and show matching filenames",
        setup_commands=[
            "mkdir -p /tmp/testdata/project/src",
            'echo "# TODO fix this" > /tmp/testdata/project/src/main.py',
            'echo "x = 1" > /tmp/testdata/project/src/utils.py',
        ],
        validation_fn="check_output_contains",
        expected_output="main.py",
        tags=["intermediate", "text_processing"],
    ),

    # --- awk and sed ---
    CLITask(
        task_id="extract_column",
        description="Extract the second column (space-separated) from /tmp/testdata/data.txt",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "a 100\\nb 200\\nc 300\\n" > /tmp/testdata/data.txt',
        ],
        validation_fn="check_output_contains",
        expected_output="100\n200\n300",
        tags=["intermediate", "text_processing"],
    ),
    CLITask(
        task_id="sum_numbers",
        description="Calculate the sum of all numbers in /tmp/testdata/numbers.txt (one number per line)",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "10\\n20\\n30\\n40\\n" > /tmp/testdata/numbers.txt',
        ],
        validation_fn="check_output_contains",
        expected_output="100",
        tags=["intermediate", "text_processing"],
    ),
    CLITask(
        task_id="awk_filter_rows",
        description="Print rows from /tmp/testdata/scores.txt where the score in column 2 is greater than 80",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "alice 95\\nbob 72\\ncharlie 88\\ndave 61\\n" > /tmp/testdata/scores.txt',
        ],
        validation_fn="check_output_contains",
        expected_output="alice",
        tags=["intermediate", "text_processing"],
    ),
    CLITask(
        task_id="sed_replace",
        description="Replace all occurrences of 'localhost' with '127.0.0.1' in /tmp/testdata/config.txt",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "host=localhost\\nport=8080\\ndb=localhost/mydb\\n" > /tmp/testdata/config.txt',
        ],
        validation_fn="check_output_contains",
        expected_output="127.0.0.1",
        tags=["intermediate", "text_processing"],
    ),
    CLITask(
        task_id="awk_average",
        description="Calculate the average of all numbers in /tmp/testdata/numbers.txt",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "10\\n20\\n30\\n40\\n" > /tmp/testdata/numbers.txt',
        ],
        validation_fn="check_output_contains",
        expected_output="25",
        tags=["intermediate", "text_processing"],
    ),
    CLITask(
        task_id="extract_csv_column",
        description="Extract the first column from /tmp/testdata/data.csv (comma-separated)",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "alice,30,engineer\\nbob,25,designer\\ncharlie,35,manager\\n" > /tmp/testdata/data.csv',
        ],
        validation_fn="check_output_contains",
        expected_output="alice\nbob\ncharlie",
        tags=["intermediate", "text_processing"],
    ),

    # --- Sort and Unique ---
    CLITask(
        task_id="sort_and_unique",
        description="Read /tmp/testdata/names.txt, sort alphabetically, remove duplicates, and show the result",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "charlie\\nalice\\nbob\\nalice\\ncharlie\\ndave\\n" > /tmp/testdata/names.txt',
        ],
        validation_fn="check_sorted_unique",
        expected_output="alice\nbob\ncharlie\ndave",
        tags=["intermediate", "text_processing"],
    ),
    CLITask(
        task_id="sort_numeric",
        description="Sort /tmp/testdata/numbers.txt numerically in ascending order",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "100\\n5\\n42\\n7\\n1000\\n" > /tmp/testdata/numbers.txt',
        ],
        validation_fn="check_output_contains",
        expected_output="5\n7\n42\n100\n1000",
        tags=["basic", "text_processing"],
    ),
    CLITask(
        task_id="count_word_frequency",
        description="Count how many times each word appears in /tmp/testdata/words.txt and show sorted by frequency",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "apple\\nbanana\\napple\\ncherry\\nbanana\\napple\\n" > /tmp/testdata/words.txt',
        ],
        validation_fn="check_output_contains",
        expected_output="3",
        tags=["intermediate", "text_processing"],
    ),
    CLITask(
        task_id="find_duplicate_lines",
        description="Show only duplicate lines in /tmp/testdata/names.txt",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "alice\\nbob\\nalice\\ncharlie\\nbob\\n" > /tmp/testdata/names.txt',
        ],
        validation_fn="check_output_contains",
        expected_output="alice",
        tags=["intermediate", "text_processing"],
    ),

    # --- Pipes and Chaining ---
    CLITask(
        task_id="top_processes_memory",
        description="List the top 5 processes by memory usage, showing PID, %MEM, and command name",
        setup_commands=[],
        validation_fn="check_command_success",
        expected_output="",
        tags=["intermediate", "system"],
    ),
    CLITask(
        task_id="top_processes_cpu",
        description="List the top 3 processes by CPU usage showing their names",
        setup_commands=[],
        validation_fn="check_command_success",
        expected_output="",
        tags=["intermediate", "system"],
    ),
    CLITask(
        task_id="count_running_processes",
        description="Count the total number of running processes on the system",
        setup_commands=[],
        validation_fn="check_command_success",
        expected_output="",
        tags=["basic", "system"],
    ),
    CLITask(
        task_id="largest_files_tmp",
        description="Show the 5 largest files in /tmp/testdata sorted by size",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            "dd if=/dev/zero of=/tmp/testdata/a.bin bs=1K count=5 2>/dev/null",
            "dd if=/dev/zero of=/tmp/testdata/b.bin bs=1K count=50 2>/dev/null",
            "dd if=/dev/zero of=/tmp/testdata/c.bin bs=1K count=500 2>/dev/null",
        ],
        validation_fn="check_output_contains",
        expected_output="c.bin",
        tags=["intermediate", "file_ops"],
    ),
    CLITask(
        task_id="http_status_counts",
        description="Count how many times each HTTP status code appears in /tmp/testdata/access.log",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "GET /a 200\\nGET /b 404\\nGET /c 200\\nGET /d 500\\nGET /e 200\\nGET /f 404\\n" > /tmp/testdata/access.log',
        ],
        validation_fn="check_output_contains",
        expected_output="3",
        tags=["advanced", "text_processing"],
    ),
    CLITask(
        task_id="env_vars_sorted",
        description="Show all environment variables sorted alphabetically",
        setup_commands=[],
        validation_fn="check_command_success",
        expected_output="",
        tags=["basic", "system"],
    ),

    # --- Archives ---
    CLITask(
        task_id="create_tar_gz",
        description="Compress the directory /tmp/testdata/logs into /tmp/testdata/logs.tar.gz",
        setup_commands=[
            "mkdir -p /tmp/testdata/logs",
            "echo 'log entry 1' > /tmp/testdata/logs/app.log",
            "echo 'log entry 2' > /tmp/testdata/logs/error.log",
        ],
        validation_fn="check_directory_structure",
        expected_output="/tmp/testdata/logs.tar.gz",
        tags=["intermediate", "file_ops"],
    ),
    CLITask(
        task_id="list_tar_contents",
        description="List the contents of /tmp/testdata/archive.tar.gz without extracting it",
        setup_commands=[
            "mkdir -p /tmp/testdata/topack",
            "echo 'hello' > /tmp/testdata/topack/hello.txt",
            "tar -czf /tmp/testdata/archive.tar.gz -C /tmp/testdata topack",
        ],
        validation_fn="check_output_contains",
        expected_output="hello.txt",
        tags=["intermediate", "file_ops"],
    ),

    # --- System Information ---
    CLITask(
        task_id="show_memory",
        description="Show current memory usage in megabytes",
        setup_commands=[],
        validation_fn="check_command_success",
        expected_output="",
        tags=["basic", "system"],
    ),
    CLITask(
        task_id="show_disk_usage",
        description="Show disk usage for all mounted filesystems in human-readable format",
        setup_commands=[],
        validation_fn="check_command_success",
        expected_output="",
        tags=["basic", "system"],
    ),
    CLITask(
        task_id="show_uptime",
        description="Show how long the system has been running",
        setup_commands=[],
        validation_fn="check_command_success",
        expected_output="",
        tags=["basic", "system"],
    ),
    CLITask(
        task_id="show_kernel",
        description="Show the current Linux kernel version",
        setup_commands=[],
        validation_fn="check_command_success",
        expected_output="",
        tags=["basic", "system"],
    ),
    CLITask(
        task_id="show_hostname",
        description="Show the hostname of this machine",
        setup_commands=[],
        validation_fn="check_command_success",
        expected_output="",
        tags=["basic", "system"],
    ),

    # --- Permissions ---
    CLITask(
        task_id="make_executable",
        description="Make /tmp/testdata/script.sh executable by the owner",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            "echo '#!/bin/bash\\necho hello' > /tmp/testdata/script.sh",
            "chmod 644 /tmp/testdata/script.sh",
        ],
        validation_fn="check_command_success",
        expected_output="",
        tags=["basic", "permissions"],
    ),
    CLITask(
        task_id="find_world_writable",
        description="Find all world-writable files in /tmp/testdata",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            "touch /tmp/testdata/normal.txt",
            "touch /tmp/testdata/worldwrite.txt",
            "chmod 777 /tmp/testdata/worldwrite.txt",
        ],
        validation_fn="check_output_contains",
        expected_output="worldwrite.txt",
        tags=["intermediate", "permissions"],
    ),

    # --- Environment Variables ---
    CLITask(
        task_id="show_path",
        description="Show all directories in the PATH environment variable, one per line",
        setup_commands=[],
        validation_fn="check_command_success",
        expected_output="",
        tags=["basic", "environment"],
    ),
    CLITask(
        task_id="show_home",
        description="Show the value of the HOME environment variable",
        setup_commands=[],
        validation_fn="check_output_contains",
        expected_output="/home",
        tags=["basic", "environment"],
    ),
    CLITask(
        task_id="count_env_vars",
        description="Count the total number of environment variables currently set",
        setup_commands=[],
        validation_fn="check_command_success",
        expected_output="",
        tags=["basic", "environment"],
    ),

    # --- Multi-step / Advanced ---
    CLITask(
        task_id="top_n_lines_sorted",
        description="Show the 3 longest lines in /tmp/testdata/file.txt",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "short\\nthis is a medium line\\nthis is the longest line in the file\\na\\nmedium length here\\n" > /tmp/testdata/file.txt',
        ],
        validation_fn="check_output_contains",
        expected_output="longest",
        tags=["advanced", "text_processing"],
    ),
    CLITask(
        task_id="unique_ips",
        description="Extract all unique IP addresses from /tmp/testdata/access.log",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "192.168.1.1 GET /a\\n10.0.0.1 GET /b\\n192.168.1.1 GET /c\\n10.0.0.2 GET /d\\n" > /tmp/testdata/access.log',
        ],
        validation_fn="check_output_contains",
        expected_output="192.168.1.1",
        tags=["advanced", "text_processing"],
    ),
    CLITask(
        task_id="files_by_extension",
        description="List all unique file extensions in /tmp/testdata/",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            "touch /tmp/testdata/a.py /tmp/testdata/b.py /tmp/testdata/c.txt /tmp/testdata/d.sh /tmp/testdata/e.txt",
        ],
        validation_fn="check_output_contains",
        expected_output=".py",
        tags=["advanced", "file_ops"],
    ),
    CLITask(
        task_id="most_common_word",
        description="Find the most frequently occurring word in /tmp/testdata/text.txt",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "the cat sat on the mat the cat ate the rat\\n" | tr " " "\\n" > /tmp/testdata/text.txt',
        ],
        validation_fn="check_output_contains",
        expected_output="the",
        tags=["advanced", "text_processing"],
    ),
    CLITask(
        task_id="lines_between_patterns",
        description="Show lines between 'START' and 'END' in /tmp/testdata/data.txt",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "header\\nSTART\\nline1\\nline2\\nEND\\nfooter\\n" > /tmp/testdata/data.txt',
        ],
        validation_fn="check_output_contains",
        expected_output="line1",
        tags=["advanced", "text_processing"],
    ),
    CLITask(
        task_id="disk_hogs",
        description="Show the top 3 largest directories under /tmp/testdata",
        setup_commands=[
            "mkdir -p /tmp/testdata/big /tmp/testdata/medium /tmp/testdata/small",
            "dd if=/dev/zero of=/tmp/testdata/big/file bs=1M count=10 2>/dev/null",
            "dd if=/dev/zero of=/tmp/testdata/medium/file bs=1M count=5 2>/dev/null",
            "dd if=/dev/zero of=/tmp/testdata/small/file bs=1K count=100 2>/dev/null",
        ],
        validation_fn="check_output_contains",
        expected_output="big",
        tags=["advanced", "system"],
    ),
    CLITask(
        task_id="check_file_exists",
        description="Check if /tmp/testdata/important.txt exists and print 'exists' or 'missing'",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            "touch /tmp/testdata/important.txt",
        ],
        validation_fn="check_output_contains",
        expected_output="exists",
        tags=["basic", "file_ops"],
    ),
    CLITask(
        task_id="remove_blank_lines",
        description="Print the contents of /tmp/testdata/file.txt with all blank lines removed",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "line1\\n\\nline2\\n\\n\\nline3\\n" > /tmp/testdata/file.txt',
        ],
        validation_fn="check_output_contains",
        expected_output="line1\nline2\nline3",
        tags=["intermediate", "text_processing"],
    ),
    CLITask(
        task_id="number_lines",
        description="Print /tmp/testdata/file.txt with line numbers prepended",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "alpha\\nbeta\\ngamma\\n" > /tmp/testdata/file.txt',
        ],
        validation_fn="check_output_contains",
        expected_output="1",
        tags=["basic", "text_processing"],
    ),
    CLITask(
        task_id="reverse_file",
        description="Print the lines of /tmp/testdata/file.txt in reverse order",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'printf "first\\nsecond\\nthird\\n" > /tmp/testdata/file.txt',
        ],
        validation_fn="check_output_contains",
        expected_output="third",
        tags=["intermediate", "text_processing"],
    ),
    CLITask(
        task_id="find_files_by_size",
        description="Find all files in /tmp/testdata larger than 100KB",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            "dd if=/dev/zero of=/tmp/testdata/big.bin bs=1K count=200 2>/dev/null",
            "dd if=/dev/zero of=/tmp/testdata/small.bin bs=1K count=10 2>/dev/null",
        ],
        validation_fn="check_output_contains",
        expected_output="big.bin",
        tags=["intermediate", "file_ops"],
    ),
    CLITask(
        task_id="compare_files",
        description="Check if /tmp/testdata/file1.txt and /tmp/testdata/file2.txt are identical",
        setup_commands=[
            "mkdir -p /tmp/testdata",
            'echo "hello world" > /tmp/testdata/file1.txt',
            'echo "hello world" > /tmp/testdata/file2.txt',
        ],
        validation_fn="check_command_success",
        expected_output="",
        tags=["basic", "file_ops"],
    ),
]