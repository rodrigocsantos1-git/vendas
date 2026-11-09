-- ========================================================
-- TABELA DE USUÁRIOS E CONTROLE DE ACESSO ADMINISTRATIVO
-- Plataforma: Vendas Barreto Corrêa
-- ========================================================

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    nome TEXT NOT NULL,
    senha_hash TEXT NOT NULL,
    perfil TEXT DEFAULT 'admin',
    ativo BOOLEAN DEFAULT true,
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    ultimo_login TIMESTAMPTZ
);

-- Habilitar RLS (Row Level Security)
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;

-- Políticas de Acesso
DROP POLICY IF EXISTS "Acesso público leitura usuarios" ON usuarios;
CREATE POLICY "Acesso público leitura usuarios" ON usuarios FOR SELECT USING (true);

DROP POLICY IF EXISTS "Acesso público atualização usuarios" ON usuarios;
CREATE POLICY "Acesso público atualização usuarios" ON usuarios FOR UPDATE USING (true);

DROP POLICY IF EXISTS "Acesso público inserção usuarios" ON usuarios;
CREATE POLICY "Acesso público inserção usuarios" ON usuarios FOR INSERT WITH CHECK (true);

-- Inserir os 2 Administradores (com senha temporária padrão 'alterar123')
INSERT INTO usuarios (email, nome, senha_hash, perfil, ativo)
VALUES 
    ('rodrigo.correa01@outlook.com', 'Rodrigo Corrêa', 'alterar123', 'admin', true),
    ('daniele_barreto@hotmail.com', 'Daniele Barreto', 'alterar123', 'admin', true)
ON CONFLICT (email) DO UPDATE 
SET nome = EXCLUDED.nome, perfil = 'admin', ativo = true;

-- ========================================================
-- COMANDOS PARA VOCÊ DEFINIR AS SUAS SENHAS DEFINITIVAS:
-- (Altere o texto dentro das aspas simples para a senha desejada e execute)
-- ========================================================

-- Definir a senha do Rodrigo:
-- UPDATE usuarios SET senha_hash = 'SUA_SENHA_AQUI' WHERE email = 'rodrigo.correa01@outlook.com';

-- Definir a senha da Daniele:
-- UPDATE usuarios SET senha_hash = 'SUA_SENHA_AQUI' WHERE email = 'daniele_barreto@hotmail.com';
