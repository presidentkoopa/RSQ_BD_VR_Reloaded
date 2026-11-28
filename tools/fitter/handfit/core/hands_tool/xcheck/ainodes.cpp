#include <assimp/Importer.hpp>
#include <assimp/scene.h>
#include <cstdio>
void walk(aiNode*n,int d){printf("%*s%s\n",d*2,"",n->mName.C_Str());for(unsigned i=0;i<n->mNumChildren;i++)walk(n->mChildren[i],d+1);}
int main(int a,char**v){Assimp::Importer imp;auto s=imp.ReadFile(v[1],0);walk(s->mRootNode,0);auto an=s->mAnimations[0];for(unsigned i=0;i<an->mNumChannels;i++)printf("CH %s %u\n",an->mChannels[i]->mNodeName.C_Str(),an->mChannels[i]->mNumRotationKeys);}
