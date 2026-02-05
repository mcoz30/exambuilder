#!/usr/bin/env python3
import re

# Read the original file
with open('index (7).html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove Supabase import and configuration
content = re.sub(
    r"import \{ createClient \} from 'https://cdn\.jsdelivr\.net/npm/@supabase/supabase-js@2/\+esm';\n// --- SUPABASE CONFIGURATION ---.*?const supabase = createClient\(supabaseUrl, supabaseKey\);",
    """// --- TURSO CONFIGURATION ---
import { createClient } from 'https://cdn.jsdelivr.net/npm/@libsql/client-web@0.4.0/+esm';

const tursoUrl = 'libsql://schoollms-mcoz30.aws-ap-south-1.turso.io';
const tursoToken = 'eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3NzAyNTM1NjQsImlkIjoiMmE2YjA5ODMtZTgwNy00OTU4LWE5YmUtZjJhMTc3ZTNmMWEzIiwicmlkIjoiNGVkMGZmZjAtMzRkNS00YzBhLTliMzMtMmRiYTgxMWUwZjE3In0.eM21FQNmO5djrGaVUptwVZjkixTjmxOCc1kbBmhI5R2khoz_Y-b0qMsQ2efymR0hR-4vUDf8VCPp8MD0jQC-AA';

const turso = createClient({
    url: tursoUrl,
    authToken: tursoToken,
});""",
    content,
    flags=re.DOTALL
)

# Remove supabaseUser from variable declarations
content = re.sub(
    r",\s*supabaseUser\s*=\s*null",
    "",
    content
)

# Replace initSupabase() with initTurso()
turso_init_function = """// --- TURSO SYNC ---
async function initTurso() {
    try {
        // Create table if not exists
        await turso.execute(`
            CREATE TABLE IF NOT EXISTS app_data (
                id TEXT PRIMARY KEY,
                data TEXT,
                updated_at TEXT
            )
        `);

        // Try to load data from Turso
        const result = await turso.execute({
            sql: 'SELECT data FROM app_data WHERE id = ?',
            args: ['master_record']
        });

        if (result.rows.length > 0 && result.rows[0].data) {
            const savedData = JSON.parse(result.rows[0].data);
            db = savedData;
            ['activities','activitySubmissions','modules','exams','examSubmissions','globalEvents'].forEach(k=>{
                if(!db[k]) db[k] = (k==='activitySubmissions'||k==='examSubmissions') ? {} : [];
            });
            if(!db.theme) db.theme = defaultData.theme;
        } else {
            // Initialize with default data
            console.log("Initializing with default data");
            await saveDB();
        }
        
        applyTheme();
        
        const l = $('loading-screen');
        if(l) {
            l.style.opacity=0;
            setTimeout(() => l.remove(), 500);
            $('app').classList.remove('opacity-0');
        }
        
        if(!currentUser) render();
    } catch (e) {
        console.error("Turso Init Error:", e);
        // If Turso is not available, fall back to local mode
        const l = $('loading-screen');
        if(l) {
            l.style.opacity=0;
            setTimeout(() => l.remove(), 500);
            $('app').classList.remove('opacity-0');
        }
        if(!currentUser) render();
    }
}"""

content = re.sub(
    r"// --- SUPABASE SYNC ---.*?initSupabase\(\);",
    turso_init_function + "\n\ninitTurso();",
    content,
    flags=re.DOTALL
)

# Replace saveDB() function
turso_save_function = """async function saveDB() {
    try {
        const dataJson = JSON.stringify(db);
        const now = new Date().toISOString();
        
        await turso.execute({
            sql: `
                INSERT INTO app_data (id, data, updated_at) 
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET 
                    data = excluded.data,
                    updated_at = excluded.updated_at
            `,
            args: ['master_record', dataJson, now]
        });

        // Show sync indicator
        const status = $('sync-status');
        if(status) {
            status.style.opacity = '1';
            setTimeout(() => status.style.opacity = '0', 2000);
        }
    } catch (e) {
        console.error("Save Error:", e);
        showToast('Failed to save data: ' + e.message, 'error');
    }
}"""

content = re.sub(
    r"async function saveDB\(\) \{.*?\}",
    turso_save_function,
    content,
    flags=re.DOTALL
)

# Remove supabaseUser assignment in loginAttempt
content = re.sub(
    r"supabaseUser = \{ id: user\.id, email: user\.username \+ '@school\.local' \};",
    "",
    content
)

# Update loading screen text
content = content.replace(
    '<p class="font-bold tracking-widest">CONNECTING...</p>',
    '<p class="font-bold tracking-widest">LOADING...</p>'
)

# Write the updated content
with open('index_turso.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Successfully converted to Turso database")
print("✓ Supabase code removed")
print("✓ Turso integration added")
print("✓ File saved as: index_turso.html")