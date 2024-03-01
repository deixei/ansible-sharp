# How to execute test cases

Run Command:

```bash
dx ansible test --name "/ansiblesharp/az"
```

The --name will look for folders with that pattern and find the collection and then identify all the test cases there.

## Results

The output will be under "test_results" folder in the directory the command what executed.

Each test will have a txt file with the output and a md file with a summary.
