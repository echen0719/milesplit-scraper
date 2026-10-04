#include <iostream>
#include <filesystem>
#include <string_view>
#include <chrono>
#include <exception>

// fastest JSON parser ever?
#include "simdjson.h"

// legit looks like Java or Python
void parseJSON(simdjson::dom::parser& parser, const std::filesystem::path& filePath) {
    simdjson::dom::element json = parser.load(filePath.string());

    size_t numRaces = json["data"].get_array().size();
    std::string_view athleteID = json["_embedded"]["athlete"]["id"].get_string();

    // std::cout << "Athlete ID: " << athleteID << " has a total of " << numRaces << " races" << std::endl;
}

int main() {
    std::filesystem::path path = "json/";
    simdjson::dom::parser parser; // creating this for every file takes effort

    try {
        int count = 0;
        auto start = std::chrono::steady_clock::now();

        if (std::filesystem::exists(path) && std::filesystem::is_directory(path)) {
            for (const auto& file : std::filesystem::directory_iterator(path)) {
                std::filesystem::path filePath = file.path();
                if (filePath.extension() == ".json") { // check if has json extension
                    count++;
                    parseJSON(parser, filePath);
                }
                else {
                    std::cout << filePath << " is not a JSON file" << std::endl;
                }

                if (count % 100000 == 0) {
                    std::cout << "Processed " << count << " files" << std::endl;
                    auto now = std::chrono::steady_clock::now();
                    std::cout << "Took " << std::chrono::duration<double>(now - start).count() << " seconds" << std::endl;
                }
            }

            std::cout << "Total number of files: " << count;
        }
        else {
            std::cerr << "Directory does not exist" << std::endl;
        }
    }
    catch (const std::exception& e) {
        std::cerr << "File/directory error because of " << e.what() << std::endl; // I could use print though...
    }

    return 0;
}