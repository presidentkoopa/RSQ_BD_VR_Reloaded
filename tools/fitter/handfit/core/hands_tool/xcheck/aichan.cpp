#include <assimp/Importer.hpp>
#include <assimp/scene.h>
#include <cstdio>
#include <cstdlib>
int main(int a,char**v){Assimp::Importer imp;auto s=imp.ReadFile(v[1],0);auto an=s->mAnimations[0];int f=atoi(v[2]);
for(unsigned i=0;i<an->mNumChannels;i++){auto c=an->mChannels[i];unsigned k=0;while(k+1<c->mNumRotationKeys&&c->mRotationKeys[k+1].mTime<=f+1e-6)k++;
auto q=c->mRotationKeys[k].mValue;aiMatrix3x3 m=q.GetMatrix();printf("%u %s %g %g %g %g %g %g %g %g %g\n",i,c->mNodeName.C_Str(),m.a1,m.a2,m.a3,m.b1,m.b2,m.b3,m.c1,m.c2,m.c3);}}
