all: 
	g++ -I/usr/include/opencv4/ -L/usr/local/lib/ main.cpp -lopencv_core