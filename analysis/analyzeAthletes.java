import java.io.File;
import java.io.IOException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

public class analyzeAthletes {
    public static void parseJSON(ObjectMapper parser, File filePath) throws IOException {
        JsonNode json = parser.readTree(filePath);

        int numRaces = json.path("data").size(); // just about 9 minutes
        String athleteID = json.path("_embedded").path("athlete").path("id").asText();

        // System.out.println("Athlete ID: " + athleteID + " has a total of " + numRaces + " races");
    }

    public static void main(String[] args) {
        File dir = new File("scraper/json/");
        ObjectMapper parser = new ObjectMapper();

        int numThreads = Runtime.getRuntime().availableProcessors();
        if (numThreads == 0) numThreads = 1;

        System.out.println("Using " + numThreads + " threads");
        ExecutorService workers = Executors.newFixedThreadPool(numThreads);

        try {
            long start = System.nanoTime();

            if (!dir.exists() || !dir.isDirectory()) {
                System.out.println("Directory no no");
                return; // realized I need to flip some booleans to save indentations
            }

            File[] files = dir.listFiles();
            if (files == null) {
                System.out.println("Couldn't properly read directory");
                return;
            }

            System.out.println("Processing a total of " + files.length + " files");
            AtomicInteger count = new AtomicInteger(0); // thread-safe
            AtomicInteger nextFile = new AtomicInteger(0);

            for (int i = 0; i < numThreads; i++) {
                workers.submit(() -> {
                    int index;

                    while ((index = nextFile.getAndIncrement()) < files.length) {
                        File file = files[index];
                        if (!file.isFile() || !file.getName().endsWith(".json")) continue;

                        try {
                            parseJSON(parser, file);
                            int completed = count.incrementAndGet();

                            if (completed % 100000 == 0) {
                                double seconds = (System.nanoTime() - start) / 1_000_000_000.0;
                                System.out.println(completed + " files took " + seconds + " seconds");
                            }
                        }
                        catch (Exception e) {
                            System.out.println("Error file: " + file);
                            System.err.println("JSON (Jackson) error because of " + e.getMessage());
                        }
                    }
                }); // the cascading staircases
            }
        }

        catch (Exception e) {
            System.out.println("File/directory error because of " + e.getMessage());
        }

        finally {
            workers.shutdown();

            /* try {
                if (!workers.awaitTermination(10, TimeUnit.MINUTES)) {
                    workers.shutdownNow();
                } // program will terminate after 10 minutes
            }
            catch (InterruptedException e) {
                workers.shutdownNow();
                Thread.currentThread().interrupt();
            }

            System.out.println("Program done!"); */
        }
    } // a few more cascading staircases
}