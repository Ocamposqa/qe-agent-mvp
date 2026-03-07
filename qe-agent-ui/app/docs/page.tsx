import fs from 'fs';
import path from 'path';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Link from 'next/link';
import { ArrowLeft, BookOpen } from 'lucide-react';

export default async function DocsPage() {
    // Determine the path to the docs folder which sits outside qe-agent-ui
    const docPath = path.join(process.cwd(), '../docs/Architecture.md');
    let content = "Documentation file not found.";
    try {
        content = fs.readFileSync(docPath, 'utf8');
    } catch (e) {
        console.error("Failed to load docs", e);
    }

    return (
        <div className="min-h-screen bg-[#f3f4f6] text-[#060b29] font-sans selection:bg-[#ffc440]/30 selection:text-white">
            {/* Header */}
            <header className="bg-white shadow border-b border-gray-200">
                <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3 text-[#03287d]">
                        <BookOpen className="w-6 h-6" />
                        <h1 className="text-xl font-black tracking-tight">SQASA | Knowledge Base</h1>
                    </div>
                    <Link href="/">
                        <button className="flex items-center gap-2 text-sm font-bold text-gray-500 hover:text-[#0032a7] transition-colors">
                            <ArrowLeft className="w-4 h-4" /> Volver a Mission Control
                        </button>
                    </Link>
                </div>
            </header>

            {/* Content Area */}
            <main className="max-w-5xl mx-auto px-6 py-10">
                <div className="bg-white p-10 rounded-xl shadow-sm border border-gray-200">
                    <article className="prose prose-blue prose-headings:text-[#03287d] prose-h1:font-black prose-h2:border-b prose-h2:pb-2 prose-a:text-[#0032a7] max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {content}
                        </ReactMarkdown>
                    </article>
                </div>
            </main>
        </div>
    );
}
