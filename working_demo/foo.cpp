#include <cstdlib>
#include <new>
#include <stdio.h>

class MyClass {
public:
    MyClass(int x);
    int x;
};

MyClass::MyClass(int x) {
    printf("you're creating a MyClass!\n");
    this->x = x;
    printf("you created a MyClass with x=%d\n", x);
}

void printMyClass(MyClass *m) {
    printf("printing MyClass: m.x=%d\n", m->x);
}
