#include <iostream>
#include "Game.h"

using namespace std;

int main(int argc, char *argv[]) {
    cout << "Hello World!" << endl;
    Game game(19, 3.5);
    game.render();
    return 0;
}
