#include <opencv2/opencv.hpp>


#include <iostream>

using namespace cv;
using namespace std;

int main() {
	VideoCapture cap(0);
	cerr << "lalalala" << endl;
	if(!cap.isOpened()) {  // check if we succeeded
		cerr << "open error" << endl;
        return -1;
	}

	Mat image;
	while (true) {
		cap >> image;
		imshow("image", image);
		waitKey(10);
	}
	cap.release();
}
