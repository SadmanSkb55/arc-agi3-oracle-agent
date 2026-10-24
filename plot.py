import matplotlib.pyplot as plt
import numpy as np

games = ['ft09','lp85','s5i5','vc33','tn36','sb26','r11l','su15',
         'ar25','cd82','ls20','sk48','tr87','tu93',
         'bp35','cn04','dc22','ka59','lf52','sc25']
counts = [8,2,4,2,11,4,256,224, 4,4,4,4,4,4, 12,7,6,6,9,13]
colors = ['#2196F3']*8 + ['#4CAF50']*6 + ['#FF9800']*6

plt.figure(figsize=(14,5))
plt.bar(games, counts, color=colors)
plt.yscale('log')
plt.xticks(rotation=45, ha='right')
plt.ylabel('Valid actions (log scale)')
plt.title('Oracle-pruned action space per public game')
plt.tight_layout()
#plt.savefig('fig2_action_space.pdf')
plt.savefig('fig2.png', dpi=300)


output = os.path.abspath("fig2.png")
plt.savefig(output, dpi=300, bbox_inches="tight")
plt.close()

print("Saved to:", output)
print("File exists:", os.path.exists(output))