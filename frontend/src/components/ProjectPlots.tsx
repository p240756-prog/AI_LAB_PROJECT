import { BarChart3, BookOpen, Download, Image as ImageIcon, ScanLine } from 'lucide-react';
import { Button } from './ui';
import type { Analysis } from './PlantLab';

const formatScore=(value:number)=>`${(value*100).toFixed(1)}%`;
const readable=(value:string)=>value.replace(/_/g,' ').replace(/\s+/g,' ').trim();

export function ProjectPlots({result,preview,onClassify}:{result:Analysis|null;preview:boolean;onClassify:()=>void}){
 const scores=result?.predictions||[];
 const otherScore=Math.max(0,1-scores.reduce((sum,p)=>sum+p.score,0));
 return <section className="lab-plots-page">
  <div className="lab-heading"><div><h1>See the classification clearly.</h1><p>Explore the current class scores and the figures saved in the project notebook.</p></div><span className="lab-count-badge">VGG19 image classifier</span></div>
  <section className="lab-plot-panel" aria-labelledby="score-chart-title">
   <div className="lab-plot-panel-heading"><div><span className="lab-section-icon"><BarChart3 size={20}/></span><h2 id="score-chart-title">Current classification scores</h2></div><span>0–100% class-score scale</span></div>
   <p className="lab-plot-intro">Each score belongs to a crop-and-condition class. It is not the percentage of diseased leaf area, disease severity, or the model’s measured accuracy.</p>
   {result?<>
    <div className="lab-full-score-chart" role="img" aria-label={`Top three class scores from VGG19. ${scores.map(p=>`${readable(p.crop)}, ${readable(p.condition)}: ${formatScore(p.score)}`).join('. ')}. Other classes combined: ${formatScore(otherScore)}.`}>
     <div className="lab-score-axis"><span>0%</span><span>25%</span><span>50%</span><span>75%</span><span>100%</span></div>
     {scores.map((p,i)=><div className="lab-full-score-row" key={p.class_index}><div><span><strong>{readable(p.crop)}</strong><small>{readable(p.condition)}</small></span><b>{formatScore(p.score)}</b></div><div className="lab-full-score-track"><span className={i===0?'top-score':''} style={{width:`${p.score*100}%`}}/></div></div>)}
     <div className="lab-full-score-row lab-other-scores"><div><span><strong>Other 33 classes combined</strong><small>Combined remainder, not a single class</small></span><b>{formatScore(otherScore)}</b></div><div className="lab-full-score-track"><span style={{width:`${otherScore*100}%`}}/></div></div>
    </div>
    <table className="lab-score-table"><caption>Accessible score table for the latest classification</caption><thead><tr><th scope="col">Crop class</th><th scope="col">Condition class</th><th scope="col">Model score</th></tr></thead><tbody>{scores.map(p=><tr key={p.class_index}><td>{readable(p.crop)}</td><td>{readable(p.condition)}</td><td>{formatScore(p.score)}</td></tr>)}</tbody></table>
    <p className="lab-plot-note">The chart shows the three scores returned by the model service. Scores across all 36 classes total approximately 100%. A highest-scoring class is a tentative match, not a confirmed diagnosis.</p>
   </>:<div className="lab-plot-empty"><BarChart3 size={35}/><h3>No classification to plot yet</h3><p>Classify a leaf first. Its actual returned scores will appear here.</p><Button onClick={onClassify}><ScanLine size={17}/>Classify a leaf</Button></div>}
  </section>
  <section className="lab-notebook-section" aria-labelledby="notebook-plots-title"><div className="lab-reference-heading"><div><h2 id="notebook-plots-title">Original notebook plots</h2><p>Three saved Matplotlib figures from the notebook’s training-image preview.</p></div><span className="lab-notebook-source"><BookOpen size={16}/>Saved project outputs</span></div>
   <div className="lab-plot-explanation"><ImageIcon size={21}/><p><strong>What these figures show</strong>They display preprocessed training images. The unusual colors are caused by displaying those arrays as RGB images; they do not identify diseased regions or measure severity. The notebook stores no class label on these figures.</p></div>
   {preview?<div className="lab-plot-empty lab-local-plots"><BookOpen size={32}/><h3>Notebook figures are available in the local app</h3><p>The original project figures stay with your local project files. They are not uploaded to the design canvas.</p></div>:<div className="lab-notebook-grid">{[1,2,3].map(i=><figure className="lab-notebook-figure" key={i}><div><img src={`/notebook-plots/training-sample-${i}.png`} alt={`Original Matplotlib training-image preview ${i}, showing a preprocessed leaf array with pixel axes`}/></div><figcaption><span><strong>Training image preview {i}</strong><small>Original saved notebook figure</small></span><a href={`/notebook-plots/training-sample-${i}.png`} download={`notebook-training-preview-${i}.png`} aria-label={`Download original notebook figure ${i}`}><Download size={17}/></a></figcaption></figure>)}</div>}
   <p className="lab-plot-note">No saved accuracy/loss curves or confusion matrix were found in this notebook. These image previews are not model-performance plots.</p>
  </section>
 </section>;
}
