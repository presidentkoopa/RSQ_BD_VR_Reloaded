// Cross-check: skin the FBX with assimp's own importer at a given frame, write verts (mesh index, frame) to stdout.
#include <assimp/Importer.hpp>
#include <assimp/scene.h>
#include <assimp/postprocess.h>
#include <cstdio>
#include <cstdlib>
#include <map>
#include <string>
#include <vector>
static aiMatrix4x4 interp(const aiNodeAnim* c,double t){
  auto pick=[&](auto* k,unsigned n){unsigned i=0;while(i+1<n&&k[i+1].mTime<=t)i++;return i;};
  aiVector3D p=c->mPositionKeys[pick(c->mPositionKeys,c->mNumPositionKeys)].mValue;
  aiVector3D s=c->mScalingKeys[pick(c->mScalingKeys,c->mNumScalingKeys)].mValue;
  unsigned i=pick(c->mRotationKeys,c->mNumRotationKeys); aiQuaternion q=c->mRotationKeys[i].mValue;
  if(i+1<c->mNumRotationKeys){double t0=c->mRotationKeys[i].mTime,t1=c->mRotationKeys[i+1].mTime; if(t1>t0&&t>t0){aiQuaternion o;aiQuaternion::Interpolate(o,q,c->mRotationKeys[i+1].mValue,(float)((t-t0)/(t1-t0)));q=o;}}
  return aiMatrix4x4(s,q,p);
}
std::map<std::string,aiMatrix4x4> G; std::map<std::string,const aiNodeAnim*> CH;
void walk(aiNode* n,aiMatrix4x4 P,double t){
  aiMatrix4x4 L=n->mTransformation; auto it=CH.find(n->mName.C_Str()); if(it!=CH.end()) L=interp(it->second,t);
  aiMatrix4x4 W=P*L; if(!G.count(n->mName.C_Str())) G[n->mName.C_Str()]=W; for(unsigned i=0;i<n->mNumChildren;i++) walk(n->mChildren[i],W,t);
}
int main(int a,char**v){
  Assimp::Importer imp; const aiScene* s=imp.ReadFile(v[1],0);
  if(!s){fprintf(stderr,"%s\n",imp.GetErrorString());return 1;}
  int mi=atoi(v[2]); double frame=atof(v[3]);
  fprintf(stderr,"meshes %u anims %u\n",s->mNumMeshes,s->mNumAnimations);
  const aiAnimation* an=s->mNumAnimations?s->mAnimations[0]:nullptr;
  double tps=an&&an->mTicksPerSecond>0?an->mTicksPerSecond:1;
  if(an && frame>=0){fprintf(stderr,"anim %s dur %f tps %f ch %u\n",an->mName.C_Str(),an->mDuration,an->mTicksPerSecond,an->mNumChannels); for(unsigned i=0;i<an->mNumChannels;i++) if(!CH.count(an->mChannels[i]->mNodeName.C_Str())) CH[an->mChannels[i]->mNodeName.C_Str()]=an->mChannels[i];}
  walk(s->mRootNode,aiMatrix4x4(),frame/60.0*tps);
  const aiMesh* m=s->mMeshes[mi];
  fprintf(stderr,"mesh %s verts %u bones %u\n",m->mName.C_Str(),m->mNumVertices,m->mNumBones);
  std::vector<aiVector3D> out(m->mNumVertices,aiVector3D(0,0,0)); std::vector<float> ws(m->mNumVertices,0);
  // express in the frame of the bone named v[4]
  aiMatrix4x4 Fi; bool haveF=false;
  for(unsigned b=0;b<m->mNumBones;b++){ const aiBone* B=m->mBones[b]; aiMatrix4x4 M=G[B->mName.C_Str()]*B->mOffsetMatrix;
    if(a>4 && std::string(B->mName.C_Str())==v[4]){Fi=G[B->mName.C_Str()];Fi.Inverse();haveF=true;}
    for(unsigned k=0;k<B->mNumWeights;k++){auto& w=B->mWeights[k]; out[w.mVertexId]+=(M*m->mVertices[w.mVertexId])*w.mWeight; ws[w.mVertexId]+=w.mWeight;}}
  for(unsigned i=0;i<m->mNumVertices;i++){aiVector3D p=out[i]/(ws[i]>0?ws[i]:1); if(haveF)p=Fi*p; printf("%g %g %g\n",p.x,p.y,p.z);}
}
