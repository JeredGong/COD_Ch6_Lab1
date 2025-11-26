#include "thread_timing.h"

#ifdef ENABLE_THREAD_TIMING

#include <cstdio>
#include <mutex>
#include <string>
#include <vector>

namespace ThreadTiming {

struct Sample {
    int threadId = 0;
    double startMs = 0.0;
    double endMs = 0.0;
    double durationMs = 0.0;
};

struct GlobalState {
    int runId = 0;
    int numThreads = 0;
    int runCounter = 0;
    std::string label;
    std::string outputPath = "thread_timings.csv";
    std::vector<Sample> samples;
    std::mutex mutex;
};

static GlobalState& state() {
    static GlobalState s;
    return s;
}

static bool fileHasContent(const std::string& path) {
    std::FILE* fp = std::fopen(path.c_str(), "r");
    if (!fp) return false;
    int ch = std::fgetc(fp);
    std::fclose(fp);
    return ch != EOF;
}

void setOutputPath(const std::string& path) {
    state().outputPath = path;
}

void setRunLabel(const std::string& label) {
    std::lock_guard<std::mutex> lock(state().mutex);
    state().label = label;
}

void beginRun(int numThreads) {
    GlobalState& s = state();
    std::lock_guard<std::mutex> lock(s.mutex);
    s.samples.clear();
    s.numThreads = numThreads;
    s.runId = ++s.runCounter;
}

void recordSample(int threadId, double startSeconds, double endSeconds) {
    GlobalState& s = state();
    std::lock_guard<std::mutex> lock(s.mutex);
    Sample sample;
    sample.threadId = threadId;
    sample.startMs = startSeconds * 1000.0;
    sample.endMs = endSeconds * 1000.0;
    sample.durationMs = (endSeconds - startSeconds) * 1000.0;
    s.samples.push_back(sample);
}

void endRun() {
    GlobalState& s = state();
    std::vector<Sample> localSamples;
    std::string label;
    int runId;
    int numThreads;

    {
        std::lock_guard<std::mutex> lock(s.mutex);
        if (s.samples.empty()) return;
        localSamples = s.samples;
        label = s.label;
        runId = s.runId;
        numThreads = s.numThreads;
    }

    bool needHeader = !fileHasContent(s.outputPath);
    std::FILE* fp = std::fopen(s.outputPath.c_str(), "a");
    if (!fp) {
        std::perror("thread_timings fopen");
        return;
    }

    if (needHeader) {
        std::fprintf(fp, "run_id,label,num_threads,thread_id,start_ms,end_ms,duration_ms\n");
    }

    for (const auto& sample : localSamples) {
        std::fprintf(fp,
                     "%d,%s,%d,%d,%.6f,%.6f,%.6f\n",
                     runId,
                     label.c_str(),
                     numThreads,
                     sample.threadId,
                     sample.startMs,
                     sample.endMs,
                     sample.durationMs);
    }

    std::fclose(fp);
}

}  // namespace ThreadTiming

#endif  // ENABLE_THREAD_TIMING
