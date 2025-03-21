
export interface CriteriaItem {
  id: string;
  name: string;
  description: string;
  score: number;
  maxScore: number;
  feedback: string;
}

export interface DesignEvaluation {
  id: string;
  fileName: string;
  uploadDate: Date;
  totalScore: number;
  maxPossibleScore: number;
  criteria: CriteriaItem[];
  overallFeedback: string;
  status: 'completed' | 'processing' | 'error';
}

export const mockEvaluationResults = (fileName: string): DesignEvaluation => {
  // This is a mock function that would be replaced with actual API call
  const criteria = [
    {
      id: '1',
      name: 'Visual Hierarchy',
      description: 'Effective use of size, color, and placement to guide attention',
      score: Math.floor(Math.random() * 5) + 1,
      maxScore: 5,
      feedback: 'Good use of hierarchy but consider improving contrast between primary and secondary elements.'
    },
    {
      id: '2',
      name: 'Typography',
      description: 'Appropriate font choices, sizing, and readability',
      score: Math.floor(Math.random() * 5) + 1,
      maxScore: 5,
      feedback: 'Font pairing works well, but body text could be larger for better readability.'
    },
    {
      id: '3',
      name: 'Color Scheme',
      description: 'Color harmony, contrast, and brand alignment',
      score: Math.floor(Math.random() * 5) + 1,
      maxScore: 5,
      feedback: 'Color palette is cohesive and aligns with brand guidelines.'
    },
    {
      id: '4',
      name: 'Layout & Spacing',
      description: 'Effective use of whitespace and grid systems',
      score: Math.floor(Math.random() * 5) + 1,
      maxScore: 5,
      feedback: 'Good spacing overall, but consider adding more whitespace around key content areas.'
    },
    {
      id: '5',
      name: 'Consistency',
      description: 'Consistent use of design elements throughout',
      score: Math.floor(Math.random() * 5) + 1,
      maxScore: 5,
      feedback: 'Design system application is mostly consistent with a few minor deviations.'
    }
  ];

  const totalScore = criteria.reduce((sum, item) => sum + item.score, 0);
  const maxPossibleScore = criteria.reduce((sum, item) => sum + item.maxScore, 0);

  return {
    id: Math.random().toString(36).substring(2, 9),
    fileName,
    uploadDate: new Date(),
    totalScore,
    maxPossibleScore,
    criteria,
    overallFeedback: `Overall, the design demonstrates good quality with a score of ${totalScore}/${maxPossibleScore}. There are opportunities to improve visual hierarchy and layout spacing.`,
    status: 'completed'
  };
};
