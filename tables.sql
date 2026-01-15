CREATE TABLE books (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    author TEXT,
    language TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE hadiths (
    id SERIAL PRIMARY KEY,
    book_id TEXT REFERENCES books(id),
    hadith_no INTEGER NOT NULL,
    hadith_text TEXT NOT NULL,
    UNIQUE (book_id, hadith_no)
);
