"""Add generic profiles, multi-game profiles, parties and join requests.

Additive and non-destructive. Legacy CS2 data is retained and backfilled.
"""
from alembic import op

revision = "20260814_03"
down_revision = "20260809_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    DO $$ BEGIN CREATE TYPE game_id AS ENUM ('cs2','valorant','standoff2'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    DO $$ BEGIN CREATE TYPE party_status AS ENUM ('OPEN','FULL','CLOSED','EXPIRED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    DO $$ BEGIN CREATE TYPE party_member_role AS ENUM ('OWNER','MEMBER'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    DO $$ BEGIN CREATE TYPE party_request_status AS ENUM ('PENDING','ACCEPTED','REJECTED','CANCELLED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

    CREATE TABLE IF NOT EXISTS user_profiles (
      id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
      display_name VARCHAR(128) NOT NULL, avatar_url TEXT, birth_year INTEGER, country_code VARCHAR(2),
      bio VARCHAR(500) NOT NULL DEFAULT '', languages JSONB NOT NULL DEFAULT '[]', microphone BOOLEAN,
      playstyle VARCHAR(32), preferred_schedule VARCHAR(80), created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS game_profiles (
      id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, game game_id NOT NULL,
      nickname VARCHAR(64) NOT NULL, primary_role VARCHAR(32), secondary_role VARCHAR(32), rank_label VARCHAR(64),
      rank_value INTEGER, region VARCHAR(32), is_active BOOLEAN NOT NULL DEFAULT TRUE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      CONSTRAINT uq_game_profile_user_game UNIQUE(user_id,game)
    );
    CREATE TABLE IF NOT EXISTS parties (
      id SERIAL PRIMARY KEY, owner_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, game game_id NOT NULL,
      title VARCHAR(80) NOT NULL, mode VARCHAR(32) NOT NULL, capacity INTEGER NOT NULL,
      vibe INTEGER NOT NULL DEFAULT 50, language VARCHAR(16), mic_required BOOLEAN NOT NULL DEFAULT FALSE,
      rank_min INTEGER, rank_max INTEGER, description VARCHAR(500) NOT NULL DEFAULT '', status party_status NOT NULL DEFAULT 'OPEN',
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), expires_at TIMESTAMPTZ NOT NULL
    );
    CREATE TABLE IF NOT EXISTS party_members (
      id SERIAL PRIMARY KEY, party_id INTEGER NOT NULL REFERENCES parties(id) ON DELETE CASCADE,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, role party_member_role NOT NULL,
      joined_at TIMESTAMPTZ NOT NULL DEFAULT now(), CONSTRAINT uq_party_member UNIQUE(party_id,user_id)
    );
    CREATE TABLE IF NOT EXISTS party_requests (
      id SERIAL PRIMARY KEY, party_id INTEGER NOT NULL REFERENCES parties(id) ON DELETE CASCADE,
      requester_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      status party_request_status NOT NULL DEFAULT 'PENDING', created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), CONSTRAINT uq_party_request UNIQUE(party_id,requester_user_id)
    );
    CREATE INDEX IF NOT EXISTS ix_parties_discover ON parties(game,status,created_at DESC);
    CREATE INDEX IF NOT EXISTS ix_parties_expires_at ON parties(expires_at);
    CREATE INDEX IF NOT EXISTS ix_party_members_user_id ON party_members(user_id);
    CREATE INDEX IF NOT EXISTS ix_party_requests_inbox ON party_requests(status,created_at DESC);

    INSERT INTO user_profiles(user_id,display_name,avatar_url,birth_year,country_code,bio,languages,microphone,playstyle,preferred_schedule)
    SELECT u.id, COALESCE(NULLIF(c.faceit_nickname,''), NULLIF(concat_ws(' ',u.first_name,u.last_name),''), 'Player'),
      COALESCE(c.avatar_url,u.photo_url),c.birth_year,c.country_code,COALESCE(c.bio,''),COALESCE(c.languages,'[]'),
      c.microphone,c.playstyle,c.schedule FROM users u LEFT JOIN cs2_profiles c ON c.user_id=u.id
    ON CONFLICT(user_id) DO NOTHING;
    INSERT INTO game_profiles(user_id,game,nickname,primary_role,secondary_role,rank_label,rank_value,region,is_active)
    SELECT c.user_id,'cs2',c.faceit_nickname,c.primary_role,c.secondary_role,
      CASE WHEN c.skill_level IS NULL THEN NULL ELSE 'FACEIT '||c.skill_level::text END,c.elo,c.country_code,TRUE
    FROM cs2_profiles c ON CONFLICT(user_id,game) DO NOTHING;
    """)


def downgrade() -> None:
    raise RuntimeError("Party product migration is intentionally irreversible to protect production data")
