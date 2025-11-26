
CXX=g++ -m64
CXXFLAGS?=
BASE_CXXFLAGS=-I../common -Iobjs/ -O3 -Wall
ALL_CXXFLAGS=$(BASE_CXXFLAGS) $(CXXFLAGS)

APP_NAME=mandelbrot
OBJDIR=objs
COMMONDIR=../common

PPM_CXX=$(COMMONDIR)/ppm.cpp
PPM_OBJ=$(addprefix $(OBJDIR)/, $(subst $(COMMONDIR)/,, $(PPM_CXX:.cpp=.o)))


default: $(APP_NAME)

.PHONY: dirs clean

dirs:
		/bin/mkdir -p $(OBJDIR)/

clean:
		/bin/rm -rf $(OBJDIR) *.ppm *~ $(APP_NAME)

OBJS=$(OBJDIR)/main.o $(OBJDIR)/mandelbrot.o $(OBJDIR)/thread_timing.o $(PPM_OBJ)

$(APP_NAME): dirs $(OBJS)
	$(CXX) $(ALL_CXXFLAGS) -o $@ $(OBJS) -lm -lpthread

$(OBJDIR)/%.o: %.cpp
	$(CXX) $< $(ALL_CXXFLAGS) -c -o $@

$(OBJDIR)/%.o: $(COMMONDIR)/%.cpp
	$(CXX) $< $(ALL_CXXFLAGS) -c -o $@

$(OBJDIR)/main.o: $(COMMONDIR)/CycleTimer.h