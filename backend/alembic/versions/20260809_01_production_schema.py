"""Production schema baseline, safe for the legacy ClutchUp database."""
from alembic import op

revision = "20260809_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE swipe_direction AS ENUM ('like','dislike')") if False else None
    op.execute("""
    DO $$ BEGIN CREATE TYPE swipe_direction AS ENUM ('like','dislike'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    CREATE TABLE IF NOT EXISTS users (
      id SERIAL PRIMARY KEY, telegram_id BIGINT NOT NULL UNIQUE, username VARCHAR(64), first_name VARCHAR(128) NOT NULL,
      last_name VARCHAR(128), photo_url TEXT, created_at TIMESTAMPTZ DEFAULT now(), updated_at TIMESTAMPTZ DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS cs2_profiles (
      id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
      faceit_player_id VARCHAR(64) NOT NULL UNIQUE, faceit_nickname VARCHAR(64) NOT NULL, avatar_url TEXT,
      elo INTEGER NOT NULL, skill_level INTEGER NOT NULL, kd_ratio DOUBLE PRECISION, role VARCHAR(32), bio VARCHAR(500) DEFAULT '',
      is_searching BOOLEAN DEFAULT TRUE, updated_at TIMESTAMPTZ DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS swipes (
      id SERIAL PRIMARY KEY, from_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      to_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, direction swipe_direction NOT NULL,
      created_at TIMESTAMPTZ DEFAULT now(), CONSTRAINT uq_swipe_pair UNIQUE(from_user_id,to_user_id)
    );
    CREATE TABLE IF NOT EXISTS lobbies (
      id SERIAL PRIMARY KEY, user_low_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      user_high_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, is_active BOOLEAN DEFAULT TRUE,
      created_at TIMESTAMPTZ DEFAULT now(), CONSTRAINT uq_lobby_pair UNIQUE(user_low_id,user_high_id)
    );
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS adr DOUBLE PRECISION;
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS hs_percent DOUBLE PRECISION;
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS win_rate DOUBLE PRECISION;
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS matches_count INTEGER;
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS primary_role VARCHAR(32);
    UPDATE cs2_profiles SET primary_role=COALESCE(primary_role, role, 'Rifler');
    ALTER TABLE cs2_profiles ALTER COLUMN primary_role SET DEFAULT 'Rifler';
    ALTER TABLE cs2_profiles ALTER COLUMN primary_role SET NOT NULL;
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS secondary_role VARCHAR(32);
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS playstyle VARCHAR(32);
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS country_code VARCHAR(2);
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS birth_year INTEGER;
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS preferred_maps JSONB NOT NULL DEFAULT '[]';
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS languages JSONB NOT NULL DEFAULT '[]';
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS microphone BOOLEAN;
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS schedule VARCHAR(80);
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS filter_elo_min INTEGER NOT NULL DEFAULT 0;
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS filter_elo_max INTEGER NOT NULL DEFAULT 4000;
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS max_elo_difference INTEGER NOT NULL DEFAULT 250;
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS filter_roles JSONB NOT NULL DEFAULT '[]';
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS filter_language VARCHAR(16);
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS filter_schedule VARCHAR(80);
    ALTER TABLE cs2_profiles ADD COLUMN IF NOT EXISTS online_only BOOLEAN NOT NULL DEFAULT FALSE;
    ALTER TABLE lobbies ADD COLUMN IF NOT EXISTS notification_sent BOOLEAN NOT NULL DEFAULT FALSE;
    ALTER TABLE lobbies ADD COLUMN IF NOT EXISTS low_seen_at TIMESTAMPTZ;
    ALTER TABLE lobbies ADD COLUMN IF NOT EXISTS high_seen_at TIMESTAMPTZ;
    CREATE INDEX IF NOT EXISTS ix_users_telegram_id ON users(telegram_id);
    CREATE INDEX IF NOT EXISTS ix_profiles_search_elo ON cs2_profiles(is_searching, elo, user_id);
    CREATE INDEX IF NOT EXISTS ix_profiles_search_role ON cs2_profiles(is_searching, primary_role, elo);
    CREATE INDEX IF NOT EXISTS ix_swipes_from_to ON swipes(from_user_id,to_user_id);
    CREATE INDEX IF NOT EXISTS ix_lobbies_low_created ON lobbies(user_low_id,created_at DESC);
    CREATE INDEX IF NOT EXISTS ix_lobbies_high_created ON lobbies(user_high_id,created_at DESC);
    """)


def downgrade() -> None:
    raise RuntimeError("The production baseline migration is intentionally irreversible")
