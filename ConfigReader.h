#ifndef CONFIG_READER
#define CONFIG_READER

#include <fstream>
#include <string>
#include <map>
#include <stdexcept>

std::map<std::string, std::string> readConfigFile(const std::string& filename = "application.conf");

#endif //CONFIG_READER
