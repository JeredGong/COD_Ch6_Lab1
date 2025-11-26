#pragma once

// Enable by defining ENABLE_THREAD_TIMING (e.g., add -DENABLE_THREAD_TIMING
// to CXXFLAGS or uncomment the line below).
// #define ENABLE_THREAD_TIMING

#include <string>

#ifdef ENABLE_THREAD_TIMING
namespace ThreadTiming {
void setOutputPath(const std::string& path);
void setRunLabel(const std::string& label);
void beginRun(int numThreads);
void recordSample(int threadId, double startSeconds, double endSeconds);
void endRun();
}
#else
namespace ThreadTiming {
inline void setOutputPath(const std::string&) {}
inline void setRunLabel(const std::string&) {}
inline void beginRun(int) {}
inline void recordSample(int, double, double) {}
inline void endRun() {}
}
#endif
