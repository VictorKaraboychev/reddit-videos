import openai
import piper
import wave
import json
import os

language = 'en_US'

model = 'lessac'
quality = 'medium'

openai.api_key = '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'


# Generate text if it doesn't exist
if (not os.path.exists('out/text.txt')):
	print(f'Generating text using gpt-3.5-turbo model...')
    
	with open('src/text-raw.txt', 'r') as file:
		raw_text = file.read()

		text = openai.ChatCompletion.create(
			model='gpt-3.5-turbo', 
			messages=[{
				'role': 'user', 
				'content': f'Review the following text and fix any punctuation, spelling and grammar errors. If there are run on sentences break them up in logical places. Do not modify the content or meaning of the text.\n\n{raw_text}'
			}]
		)['choices'][0]['message']['content']
	
		open('out/text.txt', 'w').write(text)

# Generate audio if it doesn't exist
if (not os.path.exists('out/audio.wav')):
	print(f'Generating audio using {language}-{model}-{quality} model...')
		
	with open('out/text.txt', 'r') as file:
		text = file.read()

		with open('models/voices.json', 'r') as voice_config:
			voices = json.load(voice_config)
		
			voice_info = voices[f'{language}-{model}-{quality}']
			model_files = list(voice_info['files'].keys())

			voice = piper.PiperVoice.load(
				model_path=f'models/{model_files[0]}',
				config_path=f'models/{model_files[1]}'
			)

			with open('out/audio.wav', 'wb') as f:
				with wave.Wave_write(f) as wav:
					voice.synthesize(text, wav)

if (not os.path.exists('out/video.mp4')):
	wave_obj = wave.open('out/audio.wav', 'rb')
	# Audio length
	length = wave_obj.getnframes() / wave_obj.getframerate()

	print(f'Audio length: {length} seconds')