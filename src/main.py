import asyncio
import openai
import piper
from moviepy.editor import VideoClip, VideoFileClip, CompositeVideoClip, AudioClip, AudioFileClip, CompositeAudioClip, TextClip
from moviepy.video.fx import crop, resize
from nltk import tokenize, download
from pyphen import Pyphen
import wave
import json
import os
import random
import re

language = 'en_US'

model = 'lessac'
quality = 'medium'

openai.api_key = ''

tiktok_id = ''

download('punkt')

def syllables(word):
	dic = Pyphen(lang=language)
	return len(dic.inserted(word).split('-'))
 
async def main():
    # Generate text if it doesn't exist
	if (not os.path.exists('out/text.txt')):
		print(f'Generating text using gpt-3.5-turbo model...')
		
		with open('in/text.txt', 'r') as file:
			raw_text = file.read()

			text = openai.ChatCompletion.create(
				model='gpt-3.5-turbo', 
				messages=[{
					'role': 'user', 
					'content': f'Review the following text and fix any punctuation, spelling and grammar errors. If there are run on sentences break them up in logical places. Do not modify the content or meaning of the text.\n\n{raw_text}'
				}]
			).choices[0].message.content # type: ignore
		
			open('out/text.txt', 'w').write(text)
	
	# Generate audio if it doesn't exist
	if (not os.path.exists('out/audio')):
		print(f'Generating audio using {language}-{model}-{quality} model...')
	
		os.makedirs('out/audio')
			
		with open('out/text.txt', 'r') as file:
			text = file.read()
	
			sentences = tokenize.sent_tokenize(text)

			with open('models/voices.json', 'r') as voice_config:
				voices = json.load(voice_config)
			
				voice_info = voices[f'{language}-{model}-{quality}']
				model_files = list(voice_info['files'].keys())

				voice = piper.PiperVoice.load(
					model_path=f'models/{model_files[0]}',
					config_path=f'models/{model_files[1]}'
				)
	
				captions = []

				duration = 0
				i = 0
				for sentence in sentences:
					raw_words = []

					total_syllables = 0
					for word in re.sub('[^0-9a-zA-Z\s\']+', ' ', sentence).split():
						s = syllables(word)
		
						raw_words.append({
							'word': word,
							'syllables': s
						})
						total_syllables += s
		
					with open(f'out/audio/{i}.wav', 'wb') as f:
						with wave.Wave_write(f) as wav:
							voice.synthesize(sentence, wav)

							length = wav.getnframes() / wav.getframerate()
		
							words = []
		
							sentence_duration = 0
							for word in raw_words:
								word_length = (word['syllables'] / total_syllables) * length
								words.append({
									'start': duration + sentence_duration,
									'duration': word_length - 0.05,
									'text': word['word'],
								})
								sentence_duration += word_length
		
							captions.append({
								'start': duration,
								'duration': length,
								'text': sentence,
								'words': words,
							})
		
							duration += length + 0.5
					i += 1

				open('out/captions.json', 'w').write(json.dumps(captions, indent=2))
    
	# Generate video if it doesn't exist
	if (not os.path.exists('out/video')):
		print(f'Generating video...')
	
		os.makedirs('out/video')
	
		with open('out/captions.json', 'r') as file:
			captions = json.load(file)

			duration = captions[-1]['start'] + captions[-1]['duration']
	
			with VideoFileClip('in/video.mp4') as source_video:
				# Choose a random segment of the video that is as long as the audio
				segment_start = random.uniform(0, source_video.duration - duration)

				# Crop the video
				video: VideoClip = source_video.without_audio()
				video = video.subclip(segment_start, segment_start + duration)

				# Resize the video to 1080p
				resize.resize(video, width=1920)

				# Add the audio   
				audio_clips = []
				for i in range(len(captions)):
					audio_clips.append(AudioFileClip(f'out/audio/{i}.wav').set_start(captions[i]['start']))
		
				audio = CompositeAudioClip(audio_clips)
	
				video = video.set_audio(audio)
	
				# Add on screen captions in white text with black border, centered in the screen
				captions_clips = []

				for sentence in captions:
					for word in sentence['words']:
						text_clip: TextClip = TextClip(
							txt=word['text'],
							color='white',
							font='Alte-Haas-Grotesk-Bold',
							stroke_color='black',
							stroke_width=2,
							fontsize=100,
						)
						text_clip = text_clip.set_position(('center', 'center'))
						text_clip = text_clip.set_start(word['start'])
						text_clip = text_clip.set_duration(word['duration'])
		
						# Animate the text increasing in size slightly over the duration of the word
						resize.resize(text_clip, lambda t: 1 + 0.04 * t) 
		
						captions_clips.append(text_clip)
			
				video = CompositeVideoClip([video] + captions_clips)

				# Crop the video to create vertical video 9:16
				width = video.size[0]
				height = video.size[1]
				vertical_video: VideoClip = crop.crop(video, width=height * 9 / 16, height=height, x_center=width / 2, y_center=height / 2)

				# Save the video
				video.write_videofile(
					'out/video/full.mp4', 
					codec='libx264',
					audio=True,
					audio_codec='libmp3lame',
					fps=30,
					preset='ultrafast',
				)
				vertical_video.write_videofile(
					'out/video/vertical.mp4', 
					codec='libx264',
					audio=True,
					audio_codec='libmp3lame',
					fps=30,
					preset='ultrafast',
				)
  

if __name__ == '__main__':
	asyncio.run(main())
