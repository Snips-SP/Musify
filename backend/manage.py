import os
import shutil
import random
from werkzeug.security import generate_password_hash
from backend import create_app
from backend.extensions import db
from backend.models import User, Song, Playlist  # adjust import paths as needed

app = create_app()


# This is a placeholder for your random name generator
def generate_random_name():
    names = [
    'Late Night Drives',
    'Sunset Grooves',
    'Coffee Shop Acoustics',
    'Gym Beats',
    'Road Trip Anthems',
    'Indie Dance Party',
    'Classic Rock Anthems',
    '90s Throwbacks',
    '2000s Pop Hits',
    'Productive Morning'
    ]
    return random.choice(names)


def seed_db(min_playlists_per_user=2, max_playlists_per_user=4):
    '''
    Clears and seeds the database with two users, splits songs between them,
    and creates a random number of playlists for each user.
    '''
    with app.app_context():
        try:
            # Recreate tables and upload directory
            db.drop_all()
            db.create_all()
            shutil.rmtree(app.config['UPLOAD_FOLDER'], ignore_errors=True)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            # --- 1. Create Users ---
            markus = User(name='Markus', password=generate_password_hash('123'))
            val = User(name='Val', password=generate_password_hash('123'))
            db.session.add_all([markus, val])
            db.session.commit()

            users = [markus, val]
            all_user_songs = {user.id: [] for user in users}

            # --- 2. Split, Save, and Move Songs ---
            songs_metadata = [
                ('505', 'Arctic Monkeys', '505.mp3'),
                ('Miracle Aligner', 'The Last Shadow Puppets', 'Miracle_Aligner.mp3'),
                ('Doubt', 'Twenty One Pilots', 'Doubt.mp3'),
                ('You Are the Right One', 'Sports', 'You_Are_the_Right_One.mp3'),
                ('Roommates', 'Malcolm Todd', 'Roommates.mp3'),
                ('Elephant', 'Tame Impala ', 'Elephant.mp3'),
                ('Verbatim', 'Mother Mother', 'Verbatim.mp3')
            ]

            # Split the song metadata between the two users
            split_index = len(songs_metadata) // 2
            user_song_map = {
                markus.id: songs_metadata[:split_index],
                val.id: songs_metadata[split_index:]
            }

            for user in users:
                user_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(user.id))
                os.makedirs(user_upload_dir, exist_ok=True)

                for name, artist, original_filename in user_song_map[user.id]:
                    # Create a song entry to get an ID
                    new_song = Song(name=name, artist=artist, user_id=user.id, file_path='')
                    db.session.add(new_song)
                    db.session.commit()

                    # Define the new path and update the song record
                    new_path_relative = os.path.join(os.path.basename(app.config['UPLOAD_FOLDER']), str(user.id), f'{new_song.id}.mp3')
                    new_song.file_path = new_path_relative

                    # Copy the file from the temp folder to the new structured path
                    source_path = os.path.join(app.config['TEMP_FOLDER'], original_filename)
                    destination_path = os.path.join(app.config['UPLOAD_FOLDER'], str(user.id), f'{new_song.id}.mp3')

                    if os.path.exists(source_path):
                        shutil.copy2(source_path, destination_path)
                    else:
                        print(f'Warning: Source file not found: {source_path}')

                    all_user_songs[user.id].append(new_song)

            db.session.commit()  # Commit all song file_path updates

            # --- 3. Create and Populate Playlists ---
            for user in users:
                user_songs = all_user_songs[user.id]
                if not user_songs:
                    continue  # Skip if the user has no songs

                # Create a random number of playlists for the user
                num_playlists = random.randint(min_playlists_per_user, max_playlists_per_user)

                for _ in range(num_playlists):
                    playlist_name = None
                    # Try 20 times to find a unique name for the current playlist
                    for _ in range(20):
                        candidate_name = generate_random_name()
                        name_exists = Playlist.query.filter_by(name=candidate_name).first()
                        if not name_exists:
                            playlist_name = candidate_name
                            break  # Found a unique name, exit the inner loop

                    # If a unique name was found, create the playlist
                    if playlist_name:
                        playlist = Playlist(name=playlist_name, user_id=user.id)

                        # Add a random sample of the user's own songs
                        if user_songs:
                            num_songs_to_add = random.randint(1, len(user_songs))
                            chosen_songs = random.sample(user_songs, num_songs_to_add)
                            playlist.songs.extend(chosen_songs)

                        db.session.add(playlist)
                    else:
                        # If no unique name was found after 20 attempts, print a warning and continue
                        print(f'Warning: Could not find a unique name for user {user.id} after 20 attempts. Skipping one playlist.')
                        continue

            db.session.commit()
            print('Database cleared and seeded successfully!')

        except Exception as e:
            db.session.rollback()
            print(f'Error seeding database: {e}')


if __name__ == '__main__':
    seed_db()