#include <iostream>
#include <filesystem>
#include <string_view>
#include <thread>
#include <chrono>
#include <exception>
#include <vector>
#include <queue>
#include <mutex>

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
    /* TIL: you have to be careful in the order you define variables
        after I realized threading and simdjson problems */

    std::filesystem::path path = "json/";
    std::mutex mutex;
    std::queue<std::filesystem::path> files; // should only take <4G in memory for 17M

    // my cpu should create 20 workers
    int numThreads = std::thread::hardware_concurrency();
    if (numThreads == 0) {numThreads = 1;}

    std::vector<std::jthread> workers;
    workers.reserve(numThreads);
    std::cout << "Using " << numThreads << " threads" << std::endl;

    try {
        int count = 0;
        auto start = std::chrono::steady_clock::now();

        if (std::filesystem::exists(path) && std::filesystem::is_directory(path)) {
            for (const auto& file : std::filesystem::directory_iterator(path)) {
                std::filesystem::path filePath = file.path();
                if (filePath.extension() == ".json") { // check if has json extension
                    files.push(filePath);
                    count++;
                }
                else {
                    std::cout << filePath << " is not a JSON file" << std::endl;
                }

                if (count % 100000 == 0) {
                    std::cout << "Queued " << count << " files" << std::endl;
                    auto now = std::chrono::steady_clock::now();
                    std::cout << "Took " << std::chrono::duration<double>(now - start).count() << " seconds" << std::endl;
                }
            }

            std::cout << "Total number of files: " << count;

            for (int i = 0; i < numThreads; i++) {
                workers.emplace_back([&files, &mutex]() {
                    simdjson::dom::parser parser; // each worker has its own
                    std::filesystem::path filePath;

                    while (true) {
                        {
                            // according to what I read, this prevents one worker accidentally popping an empty vector
                            std::lock_guard<std::mutex> lock(mutex);

                            if (files.empty()) {
                                break;
                            }

                            filePath = files.front();
                            files.pop();
                        }

                        try { // worker threads need try-catch block
                            parseJSON(parser, filePath);
                        }
                        catch (const std::exception& e) {
                            std::cout << "Error file: " << filePath << std::endl;
                            std::cerr << "JSON (simdjson) error because of " << e.what() << std::endl;
                        }
                    }

                });
            }
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