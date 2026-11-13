-- Script SQL para criar a tabela de Keep-Alive no Supabase
-- Execute este script no SQL Editor do seu projeto Supabase:
-- https://supabase.com/dashboard/project/evqjlgfhdpisxxbvxelh/sql/new

CREATE TABLE IF NOT EXISTS public.keep_alive (
    id BIGSERIAL PRIMARY KEY,
    data_hora TIMESTAMPTZ DEFAULT NOW(),
    origem TEXT DEFAULT 'github-actions',
    mensagem TEXT DEFAULT 'Supabase ativo'
);

-- Habilitar RLS e permitir inserção, leitura e exclusão pública
ALTER TABLE public.keep_alive ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Acesso publico keep_alive" ON public.keep_alive;

CREATE POLICY "Acesso publico keep_alive" 
ON public.keep_alive 
FOR ALL 
TO anon, authenticated 
USING (true) 
WITH CHECK (true);
