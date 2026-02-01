#ifdef _WIN32
#include <windows.h>
#include <psapi.h>
#else
#include <sys/sysinfo.h>
#include <sys/resource.h>
#include <dirent.h>
#include <ctype.h>
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

typedef struct {
    unsigned long total_memory;
    unsigned long free_memory;
    unsigned long used_memory;
    double cpu_percent;
    int process_count;
    time_t timestamp;
} SystemStats;

SystemStats get_system_stats() {
    SystemStats stats = {0};
    stats.timestamp = time(NULL);
    
#ifdef _WIN32
    // Windows implementation
    MEMORYSTATUSEX memInfo;
    memInfo.dwLength = sizeof(MEMORYSTATUSEX);
    GlobalMemoryStatusEx(&memInfo);
    
    stats.total_memory = memInfo.ullTotalPhys;
    stats.free_memory = memInfo.ullAvailPhys;
    stats.used_memory = stats.total_memory - stats.free_memory;
    
    // Get process count
    DWORD processes[1024], needed;
    if (!EnumProcesses(processes, sizeof(processes), &needed)) {
        stats.process_count = 0;
    } else {
        stats.process_count = needed / sizeof(DWORD);
    }
#else
    // Linux implementation
    struct sysinfo info;
    if (sysinfo(&info) == 0) {
        stats.total_memory = info.totalram * info.mem_unit;
        stats.free_memory = info.freeram * info.mem_unit;
        stats.used_memory = stats.total_memory - stats.free_memory;
    }
    
    // Process count
    DIR *dir = opendir("/proc");
    if (dir) {
        struct dirent *entry;
        while ((entry = readdir(dir)) != NULL) {
            if (isdigit(entry->d_name[0])) {
                stats.process_count++;
            }
        }
        closedir(dir);
    }
#endif
    
    // Simple CPU usage calculation
    static unsigned long long last_total = 0, last_idle = 0;
    
#ifdef _WIN32
    // Windows CPU stats would go here
    stats.cpu_percent = 0.0;  // Simplified
#else
    FILE *fp = fopen("/proc/stat", "r");
    if (fp) {
        unsigned long long user, nice, system, idle;
        fscanf(fp, "cpu %llu %llu %llu %llu", &user, &nice, &system, &idle);
        fclose(fp);
        
        unsigned long long total = user + nice + system + idle;
        unsigned long long total_diff = total - last_total;
        unsigned long long idle_diff = idle - last_idle;
        
        if (last_total != 0 && total_diff > 0) {
            stats.cpu_percent = 100.0 * (total_diff - idle_diff) / total_diff;
        }
        
        last_total = total;
        last_idle = idle;
    }
#endif
    
    return stats;
}

// JSON output for Python consumption
char* stats_to_json(SystemStats stats) {
    char *json = malloc(512);
    if (!json) return NULL;
    
    snprintf(json, 512,
        "{\"timestamp\":%ld,\"memory\":{\"total\":%lu,\"used\":%lu,\"free\":%lu},"
        "\"cpu_percent\":%.2f,\"process_count\":%d}",
        stats.timestamp, stats.total_memory, stats.used_memory, stats.free_memory,
        stats.cpu_percent, stats.process_count);
    
    return json;
}

// Daemon mode for continuous monitoring
void monitor_daemon() {
    printf("Cortex System Monitor starting...\n");
    
    while (1) {
        SystemStats stats = get_system_stats();
        char *json = stats_to_json(stats);
        
        // Write to pipe for Python to read
        FILE *pipe = fopen("/tmp/cortex_stats", "w");
        if (pipe) {
            fprintf(pipe, "%s\n", json);
            fclose(pipe);
        }
        
        free(json);
        sleep(5);  // Update every 5 seconds
    }
}

int main(int argc, char *argv[]) {
    if (argc > 1 && strcmp(argv[1], "--daemon") == 0) {
        monitor_daemon();
    } else {
        // One-shot stat output
        SystemStats stats = get_system_stats();
        char *json = stats_to_json(stats);
        printf("%s\n", json);
        free(json);
    }
    
    return 0;
}