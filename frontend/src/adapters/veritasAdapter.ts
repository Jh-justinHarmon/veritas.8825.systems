// Adapter: Transform hardcoded-data.ts → VeritasAnswer format (Replit contract)

import { HARDCODED_RESPONSE } from '../hardcoded-data';

export interface VeritasIdea {
  id: string;
  concept: string;
  paragraphs: string[];
  sourceIds: string[];
}

export interface VeritasSource {
  label: string;
  short: string;
  type: 'docs' | 'practice' | 'failure';
  meta: string;
  excerpt: string;
}

export interface VeritasAnswer {
  question: string;
  ideas: VeritasIdea[];
  sources: Record<string, VeritasSource>;
}

// Map tier to knowledge type
function tierToType(tier: number): 'docs' | 'practice' | 'failure' {
  if (tier === 1) return 'docs';
  if (tier === 2) return 'practice';
  return 'failure';
}

// Transform sections[] → ideas[]
function transformSections(): VeritasIdea[] {
  return HARDCODED_RESPONSE.sections.map((section) => {
    // Generate kebab-case ID from title
    const id = section.title.toLowerCase().replace(/\s+/g, '-');
    
    // Use title as concept (one-sentence thesis)
    const concept = section.title === 'Core Answer' 
      ? 'Claude selects tools based on how well your tool definitions match the user\'s intent'
      : section.title === 'Implementation Insight'
      ? 'Reliable tool use comes down to making your tools unambiguous and easy for the model to reason about'
      : 'Most tool use failures come from subtle design issues that aren\'t obvious from the docs';
    
    // Split content into paragraphs and transform citations [1][2] → [source-1][source-2]
    const paragraphs = section.content
      .split('\n\n')
      .map(para => para.replace(/\[(\d+)\]/g, (_, num) => `[source-${num}]`));
    
    // Extract source IDs from citations
    const sourceIds = section.citations.map(citId => `source-${citId}`);
    
    return {
      id,
      concept,
      paragraphs,
      sourceIds
    };
  });
}

// Transform citations[] → sources{}
function transformSources(): Record<string, VeritasSource> {
  const sources: Record<string, VeritasSource> = {};
  
  HARDCODED_RESPONSE.citations.forEach(citation => {
    const sourceId = `source-${citation.id}`;
    
    // Extract short URL from full URL
    const short = citation.url
      .replace(/^https?:\/\//, '')
      .replace(/\/$/, '')
      .split('/').slice(0, 2).join('/');
    
    sources[sourceId] = {
      label: citation.sourceName,
      short,
      type: tierToType(citation.tier),
      meta: '2024', // Default meta
      excerpt: citation.text.substring(0, 200) + (citation.text.length > 200 ? '...' : '')
    };
  });
  
  return sources;
}

// Main adapter function
export function getHardcodedAnswer(): VeritasAnswer {
  return {
    question: 'Why is Claude calling the wrong tool or using incorrect parameters?',
    ideas: transformSections(),
    sources: transformSources()
  };
}
