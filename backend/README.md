# Ryzen-Transcription Backend
This is a backend built to run deliver real-time subtitles using RyzenAI.\
It is built upon [Real Time Whisper Transcription](https://github.com/davabase/whisper_real_time) and [AMD Transformers demo](https://account.amd.com/en/forms/downloads/ryzen-ai-software-platform-xef.html?filename=transformers_2308.zip).

## Installation
1. Follow the instructions and install the Ryzen-AI Software
    - https://ryzenai.docs.amd.com/en/latest/inst.html
    - Re-use or duplicate the conda environment created in the installation process.
2. Install Additional Dependencies
    - A non-exhaustive list of dependencies can be found in the `additional_requirements.txt` file
    ```powershell
      cd backend
      pip install -r additional_requirements.txt
    ```
3. Build the whisper-onnx model
    ```powershell
      ./build.ps1
    ```

## Running the Backend
1. Start the backend API webserver.
    ```powershell
      python start_webserver.py
    ```
2. You should be able to access the api documentation at `http://localhost:6789/docs`

## Troubleshooting:
If you run into the error
```powershell
InternalError: Check failed: *it != type_key2index_.end()) is false: Cannot find type tir.Load. Did you forget to register the node by TVM_REGISTER_NODE_TYPE ?
```
Then run build.ps1 again
```powershell
./build.ps1
```
- It may spit out an additional error:
  ```powershell
  The process cannot access the file because it is being used by another process:...
  build whisper-onnx demo failed.
  ```
  This should not cause any issues, and you can try running the backend again.

# whisper-onnx
These are the original instructions for the whisper-onnx project.\
They have been included here for reference.

This example shows how to deploy Whisper models by using onnxruntime framework on custom AIE+CPU backends.

This repository has been reimplemented with ONNX using [PINTO0309/whisper-onnx-cpu](https://github.com/PINTO0309/whisper-onnx-cpu.git) as a reference.

## 1. Build & install
This Whisper demo depends on TVM and VAIP toolchains, both they would be built in this step.

### 1.1 Prepare conda environment
- First of all, please ensure that you have installed AMD-IPU driver successfully.
- Create a new conda environment based on py39 and install some packages, then activate it:
```powershell
cd whisper-onnx
conda env create --name your_conda_env_name -f environment.yml
conda activate your_conda_env_name
```

### 1.2 Build whisper-onnx
- Continue to use the above conda environment then execute following command, these processes would be done in this step:
  - Download and install vaip and onnxruntime packages and replace some necessary files;
  - Download onnx model files and preprocessed LibriSpeech dataset;
  - Build the whisper app then you could run it directly.
```powershell
cd whisper-onnx
# please use powershell to execute this commend
./build.ps1
```

- When the whisper app is built success, the console output would be looked like following:
```powershell
...
build whisper-onnx demo success.
Build whisper-onnx success, you could run it now.
```

- If you have any of the following problems when running `build.ps1`, these solutions maybe could help you:
  - Issue which is looked like: `File xxxx\build.ps1 cannot be loaded. The file xxxx\build.ps1 is not digitally signed. ...`, it is caused by permission of system and you could do this to solve it:
  ```powershell
  # execute this command, then try to run `build.ps1` again.
  Unblock-File -Path '.\build.ps1'
  ```
  - `download and extract dependencies failed.` printed in console, these maybe since web issue when downloading packages from url or permission issue when extracting compress files. Please check:
    - Check if you could access those web links which are listed in `build.yml` file;
    - Check if there has permission to new a folder or decompress files in your system.
  - `install xxx wheel failed.` issue, please ensure you didn't install other packages since it would cause some package conflicts.


## 2. Transcribe audios
In this release version, it could transcribe audio which duration shorter than 10.24 seconds well, otherwise the audio would be cutted into several parts and the first 10.24 seconds part could be decoded normally, but the rest maybe not decoded well. Therefore I suggest that you transcribe those audios which duration less than 10.24 seconds. One more limitation is that it could recognize English speech only for this release. 
### 2.1 Supported CLI options
- Execute this command to fetch all supported modes:
```powershell
whisper -h
```
- Supported options are shown as below:
```powershell
whisper -h
usage: whisper [-h] [--audio [AUDIO ...]] [--output_dir OUTPUT_DIR] [--target {aie-cpu,cpu-aie}] [--librispeech LIBRISPEECH] [--test_num TEST_NUM]

optional arguments:
  -h, --help            show this help message and exit
  --audio [AUDIO ...]   Specify the path to at least one or more audio files (wav, mp4, mp3, etc.). e.g. --audio aaa.mp4 bbb.mp3 ccc.mp4 (default: None)
  --output_dir OUTPUT_DIR, -o OUTPUT_DIR
                        directory to save the outputs (default: .)
  --target {aie-cpu,cpu-aie}
                        which target to run encoder and decoder models (default: cpu-aie)
  --librispeech LIBRISPEECH
                        test WER of LibriSpeech dataset if you set path of LibriSpeech dataset. (default: None)
  --test_num TEST_NUM   dataset samples count to calculate WER, 0 means whole dataset. (default: 0)
```

- More details about `target` argument:

| options | note |
|---------|------|
|`cpu-aie`|Float encoder model would be run with ORT CPU EP, quantized decoder model run on AIE.|
|`aie-cpu`|Quantized encoder model run on AIE, float decoder model run with ORT CPU EP.|

### 2.2 Important notes before running
There are some instructions maybe could help you have a better experience:
- While any model first time running on `AIE` target, it needs several time to be compiled, about 30 minutes or more so please wait it. 
```powershell
# follow the progress bar until it come to 100%, the 60-80% step takes a long time
Compiling model: 100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 5/5 [06:40<00:00, 80.15s/it]
```
- If which model ever running on `AIE` target, the compiled model would be saved in a cache folder. So when this model running on `AIE` target again, it needn't to be compiled anymore, but it would cost time to load compiled model from local cache, about 1~2 minutes.
```powershell
# the progress bar of console ouput could indicate current status.
loading cached library
Loding cached model: 100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:01<00:00,  1.86it/s]
```
- It still might running on `CPU` even specify `AIE` to the `target` argument, since models would be fallback to `CPU` automatically if some issues are appeared in compile process. So you could use these methods to confirm if models really running on `AIE`:
  - If model running on `AIE`, the console would print log which is looked like:
  ```powershell
  ...
  [03:42:47] C:\Users\xbuild\Desktop\xj3\VAI_RT_WIN_ONNX_EP\vaip\vaip_custom_op_asr\src\custom_op.cpp:74:  Vitis AI ASR EP running xxx Nodes
  ...
  ```
  - You also could follow the progress bar of compiling model or loding cached model, it indicates the model running on `AIE` if the bar come to 100% successfully.
  - In opposite, if model fallback to `CPU`, this log would be appeared in console output, or the progress bar doesn't reach to the end:
  ```powershell
  ...
  # some error message here and then:
  fallback to OnnxRuntime CPU.
  ...
  ```

### 2.3 Decode your own audio
- You can use the `Voice Recoder` of Windows system to record your own audio or get from somewhere else, then assign the audio path to `--audio` to decode that specified audio:
```powershell
# this example means that the wav file would be run with quantized encoder onnx model on AIE and float decoder onnx model on ORT CPU EP
whisper --audio .\test_audio.m4a --target aie-cpu
```
- The console output would be as shown below, the decoding results would be saved into a text file in current path which with the same name as audio. You could specify the folder path through setting `--output_dir` and the results would be saved into this specified folder path.
```powershell
---------------------result----------------------
Prediction Result:   Hi, welcome to experience AMD IPU.
Encoder running time: 0.04s, Decoder running time: 0.36s, Other process time: 0.32s
Real time factor: 0.081, Audio duration: 8.84s, Decoding time: 0.72s
-------------------------------------------------
[Info] Save the transcribe result into .\test_audio.m4a.txt successfully.
```
- The saved text file would be looked like this:
```text
Audio file name: test_audio.m4a
Prediction:  Hi, welcome to experience AMD IPU.
Encoder running time: 0.04s, Decoder running time: 0.36s, Other process time: 0.32s
Real time factor: 0.081, Audio duration: 8.84s, Decoding time: 0.72s
```
- Remind that `Encoder running time` and `Decoding time` are not accurate enough when decode your own audios, since it is cold start without some warmup steps. So if you want to measure these time consumption, you could run with dataset follow the next chapter.

## 3. Test on LibriSpeech
LibriSpeech is a speech recognition dataset with diverse reading materials, various accents, and speakers, commonly used for speech processing research. You could test `Word Error Rate` and `Real Time Factor` on it, but remind that if which audio's duration is longer than 10 seconds, it would be skipped when testing on this dataset since the [reason mentioned above](#2-transcribe-audios).

### 3.1 Prepare dataset

- If whisper was built successfully, the librispeech dataset that we've processed would be prepared already, you could run with this dataset directly. It was preprocessed from `test-clean.tar.gz` of [original LibriSpeech](https://www.openslr.org/12/), and the audios' metainfos are included in `librispeech-test-clean-wav.json` file, it looks like following:

```json
[
  {
    "transcript": "concord returned to its place amidst the tents",
    "files": [
      {
        "channels": 1,
        "sample_rate": 16000.0,
        "bitdepth": 16,
        "bitrate": 256000.0,
        "duration": 3.505,
        "num_samples": 56080,
        "encoding": "Signed Integer PCM",
        "silent": false,
        "fname": "test-clean-wav/6930/75918/6930-75918-0000.wav",
        "speed": 1
      }
    ],
    "original_duration": 3.505,
    "original_num_samples": 56080
  },
  {
    "transcript": "the english forwarded to the french baskets of flowers of which they had made a plentiful provision to greet the arrival of the young princess the french in return invited the english to a supper which was to be given the next day",
    "files": [
      {
        "channels": 1,
        "sample_rate": 16000.0,
        "bitdepth": 16,
        "bitrate": 256000.0,
        "duration": 14.225,
        "num_samples": 227600,
        "encoding": "Signed Integer PCM",
        "silent": false,
        "fname": "test-clean-wav/6930/75918/6930-75918-0001.wav",
        "speed": 1
      }
    ],
    "original_duration": 14.225,
    "original_num_samples": 227600
  },
  ...
]
```

- You can also test with other parts of LibriSpeech, but you should preprocess them previously. You can follow these steps:
  - Download LibriSpeech from http://www.openslr.org/12/ then decompress it, e.g. `dev-clean.tar.gz`.
  - Process the extracted dataset, you can refer to the code [here](https://github.com/mlcommons/inference/tree/master/speech_recognition/rnnt/pytorch/utils), then download and execute in [WSL](https://learn.microsoft.com/en-us/windows/wsl/about) since there are some issues if running on Windows system directly: 
  ```powershell
  # change it to your own path
  python convert_librispeech.py --input_dir your_uncompressed_dataset_path --dest_dir your_output_processed_dataset_path --output_json your_output_json_path
  ```
  - It would generate processed `wav` data and JSON file as above, then you could check about it expecially the `fname` field and  test on them.

### 3.2 Go to test

- Assign the JSON file path which includes audios' metainfos and the number of test cases to `--librispeech` and `--test_num` respectively, if not assign `--test_num` or set it to 0 would test the whole dataset.
```powershell
# use our preprocessed dataset
whisper --librispeech librispeech-test-clean-wav.json --test_num 10 --target cpu-aie

# or use other part of LibriSpeech and preprocess by your own
whisper --librispeech your_output_metainfo_json --test_num 10 --target cpu-aie
```

- The console output would be as shown below, meanwhile the decoding results would be saved into a JSON in current path which is named `test_librispeech_results.json`. You also could assign `--output_dir` to specify the saved folder path.
```powershell
# Take `test_num=3` as an example
Warm up some steps...
warm up: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 3/3 [00:09<00:00,  3.16s/audio]
Warm up done.
Dataset:   0%|                                                                                                                                | 0/3 [00:00<?, ?audio/s]---------------------result----------------------
transcript:  congratulations were poured in upon the princess everywhere during her journey
prediction:  congratulations we report in the p on the princess everywhere during her journey
Encoder running time: 0.53s, Decoder running time: 0.59s, Other process time: 0.3s
real time factor: 0.284, Audio duration: 5.01s, Decoding time: 1.42s
-------------------------------------------------
Dataset:  33%|████████████████████████████████████████                                                                                | 1/3 [00:01<00:02,  1.42s/audio]---------------------result----------------------
transcript:  this has indeed been a harassing day continued the young man his eyes fixed upon his friend
prediction:  this has indeed been a harassing day continued the young man his eyes fixed upon his friend
Encoder running time: 0.54s, Decoder running time: 0.73s, Other process time: 0.36s
real time factor: 0.278, Audio duration: 5.84s, Decoding time: 1.63s
-------------------------------------------------
Dataset:  67%|████████████████████████████████████████████████████████████████████████████████                                        | 2/3 [00:03<00:01,  1.54s/audio]---------------------result----------------------
transcript:  you will be frank with me i always am
prediction:  you will be frank with me i always am
Encoder running time: 0.56s, Decoder running time: 0.39s, Other process time: 0.3s
real time factor: 0.38, Audio duration: 3.3s, Decoding time: 1.25s
-------------------------------------------------
Dataset: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 3/3 [00:04<00:00,  1.44s/audio]
WER>>>>>:0.1351, error scores: 5, total words in test set: 37, total samples: 3
RTF Average: 0.314, RTF 50%: 0.284, RTF 90%: 0.361, RTF 99%: 0.378
total encoder running time: 1.63s
total decoder running time: 1.71s
total other process time: 0.96s
Total decoding time: 4.3s
[Info] Test results are save into .\test_librispeech_results.json successfully.
```

- The saved result JSON file is looked like below and contains more information than console output:
```json
[{"Final Results": {"word error rate": 0.1351, "total test samples": 3, "error scores": 5, "total test words": 37, "RTF Average": 0.314, "RTF 50%": 0.284, "RTF 90%": 0.361, "RTF 99%": 0.378, "total decoding time": "4.3s", "total encoder running time": "1.63s", "total decoder running time": "1.71s", "total other process time": "0.96s"}}, {"fname": "test-clean-wav/6930/75918/6930-75918-0002.wav", "transcript": "congratulations were poured in upon the princess everywhere during her journey", "prediction": "congratulations we report in the p on the princess everywhere during her journey", "real time factor": 0.284, "audio duration": "5.01s", "decoding time": "1.42s", "encoder running time": "0.53s", "decoder running time": "0.59s", "other process time": "0.3s"}, {"fname": "test-clean-wav/6930/75918/6930-75918-0006.wav", "transcript": "this has indeed been a harassing day continued the young man his eyes fixed upon his friend", "prediction": "this has indeed been a harassing day continued the young man his eyes fixed upon his friend", "real time factor": 0.278, "audio duration": "5.84s", "decoding time": "1.63s", "encoder running time": "0.54s", "decoder running time": "0.73s", "other process time": "0.36s"}, {"fname": "test-clean-wav/6930/75918/6930-75918-0007.wav", "transcript": "you will be frank with me i always am", "prediction": "you will be frank with me i always am", "real time factor": 0.38, "audio duration": "3.3s", "decoding time": "1.25s", "encoder running time": "0.56s", "decoder running time": "0.39s", "other process time": "0.3s"}]
```

### 3.3 Some test results

We have some test results on test-clean dataset of LibriSpeech, the audios which duration longer than 10 seconds would be skiped as said [before](#3-test-on-librispeech). 

- The computer configuration for the test is following:

|CPU|Memory|OS Version|
|---|------|----------|
|AMD Ryzen 7 7840U w/ Radeon 780M Graphics 3.30 GHz|32GB 5600MHz|Windows 11 Pro 22H2|

- Here are the `WER` and `RTF` results under different `target` and `test_num`:

|--target|--test_num|WER|RTF Avg|RTF 50%|RTF 90%|RTF 99%|Total decoding time(s)|
|--------|----------|---|-------|-------|-------|-------|----------------------|
|aie-cpu|10|0.1389|0.334|0.315|0.407|0.444|12.92|
|aie-cpu|200|0.2011|0.326|0.314|0.415|0.5|320.09|
|aie-cpu|2007 (all)|0.2926|0.393|0.365|0.555|0.74|3737.76|
|cpu-aie|10|0.0926|4.182|1.486|4.384|26.684|153.75|
|cpu-aie|200|0.1597|2.47|1.539|2.311|30.403|2401.1|
|cpu-aie|2007 (all)|0.1901|3.122|1.666|3.03|38.606|27464.82|

## whisper-onnx original license file 
MIT License

Copyright (c) 2023 Katsuya Hyodo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.