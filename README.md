# NeedleInAVidStack

<img src="NIAVS_logo.png" width=250>

Extract, timestamp, and analyze specific content from video collections using LLM-powered audio/video processing.

## Overview

Extracting and organizing content across vast video libraries remains a laborious and manual process. NeedleInAVidStack is a lightweight streamlit app that helps you quickly analyze video libraries by converting them to audio and using Google's Gemini AI models to identify specific content. Using video and audio understanding large language models allows us to efficiently automate this process to rapidly identify and timestamp specific content from semantic descriptions across video and audio formats.

## Features

- Bulk video to audio conversion with automatic size optimization
- Support for multiple video formats (mp4, avi, mov, mkv)
- Integration with Google's Gemini AI models via:
  - Gemini API (Direct)
  - Google Cloud Vertex AI
- Customizable analysis prompts
- Automatic timestamp detection
- Built-in size management for API compliance
- Streamlit-based user interface
- Output saved as text files for easy reference and downstream processing



## Installation (uv Reccomended)

**Prerequisites**

- Python 3.10 or higher
- Access to either:
  - Google Gemini API key
  - Google Cloud Platform account with Vertex AI enabled

1. Clone the repository:
```bash
git clone https://github.com/ALucek/NeedleInAVidStack.git
cd NeedleInAVidStack
```

2. Install dependencies using [uv](https://docs.astral.sh/uv/):
```bash
uv sync
```

## Usage

1. Start the Streamlit application:
```bash
uv run src/app.py
```

2. Access the web interface at `http://localhost:8501`

3. Configure your analysis:
   - Enter or customize the analysis prompt
   - Choose between Gemini API or Vertex AI
   - Provide necessary credentials
   - Select the video folder to process

4. Click "Convert Videos to Audio" to convert your videos to the proper Audio format

5. Click "Analyze Audio Files" to run the analysis

## API Configuration

#### Using Gemini API:
- Select "Gemini API" as your API choice
- Get your API key from Google AI Studio
- Enter the API key in the web interface

#### Using Vertex AI:
1. Create a service account in your GCP project
2. Grant necessary Vertex AI permissions
3. Download the service account JSON key file
4. Configure in the web interface:
   - Select "Vertex AI" as your API choice
   - Enter your GCP Project ID
   - Specify the region (e.g., us-east1)
   - Provide path to credentials JSON file


#### Using `.streamlit/secrets.toml`

Store your credentials securely here. If present, the app will use these credentials automatically. Otherwise, users will be prompted to input them via the UI.


```toml
# Example secrets file:
GEMINI_API_KEY = "your_gemini_api_key_here"

[vertex_ai]
project_id = "your_gcp_project_id"
location = "your_gcp_location"
credentials_file = "./path/to/credentials.json"
```

*Note: Users who prefer not to use secrets.toml can manually input their credentials through the app interface.*

## Example Prompt

The default prompt template helps you structure your analysis:

```
Analyze this audio for specific examples of [target topic] - these are instances where [explain what you're looking for]. 

Please start with a brief overview of what the audio is about.

For each relevant example found, include:
- When it was mentioned (timestamp)
- What specific aspect of [target topic] was discussed
- The context and details provided
- Direct quotes from the speaker if they described it specifically

Don't include:
- General discussion about [target topic] without specific examples
- Tangential mentions or references
- Theory or hypothetical scenarios

End with your assessment: How confident are you these were genuine examples of [target topic]? Were any examples unclear or ambiguous? How reliable were the speakers in their descriptions?

If no clear examples are found, simply state that.
```

Customize this prompt based on your specific analysis needs. It is recommended to format the prompt in a Description -> Analysis -> Conclusion format to get the best performance.

## Output Structure

The tool creates two main output directories:

```
output/
├── audio/      # Converted audio files
└── analysis/   # Text files containing analysis results
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

Todo:
- Better interface
- Clean up input/output methods
- Pressure test with long/many videos
- Fix weird error when uv closes streamlit app

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) for details.
